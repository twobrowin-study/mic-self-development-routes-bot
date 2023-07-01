from spreadsheetbot.sheets.users import UsersAdapterClass

import asyncio
from gspread import utils
import numpy as np

from spreadsheetbot import (
    I18n,
    Settings,
    Keyboard,
    Registration,
    Groups,
    Report,
    Log
)

from telegram import (
    Update,
    ReplyKeyboardRemove
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

async def keyboard_key_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard_row = Keyboard.get(update.message.text)
        uid = update.effective_chat.id
        if keyboard_row.function == Keyboard.REGISTER_FUNCTION:
            user = self._get(self.selector(uid))
            await update.message.reply_markdown(
                keyboard_row.text_markdown.format(user=self.user_data_markdown(user)),
                reply_markup=self.user_data_inline_keyboard(user)
            )
        elif keyboard_row.function == Keyboard.RERUN_TEST:
            registration = Registration.first_rerun_test
            await update.message.reply_markdown(
                keyboard_row.text_markdown,
                reply_markup=registration.reply_keyboard
            )
            await self._update_record(uid, 'state', registration.state)
        elif keyboard_row.track_state == I18n.track_state_main:
            sub_track_title = self._get(self.selector(uid)).sub_track_title
            await update.message.reply_markdown(
                keyboard_row.text_markdown,
                reply_markup=Keyboard.get_reply_keyboard(sub_track_title, I18n.track_state_sub)
            )
        elif keyboard_row.track_state == I18n.track_state_sub:
            main_track_title = self._get(self.selector(uid)).main_track_title
            await update.message.reply_markdown(
                keyboard_row.text_markdown,
                reply_markup=Keyboard.get_reply_keyboard(main_track_title, I18n.track_state_main)
            )
        elif keyboard_row.send_picture == '':
            await update.message.reply_markdown(
                keyboard_row.text_markdown,
                reply_markup=Keyboard.reply_keyboard
            )
        elif keyboard_row.send_picture != '' and len(keyboard_row.text_markdown) <= 1024:
            await update.message.reply_photo(
                keyboard_row.send_picture,
                caption=keyboard_row.text_markdown,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=Keyboard.reply_keyboard
            )
        elif keyboard_row.send_picture != '' and len(keyboard_row.text_markdown) > 1024:
            await update.message.reply_markdown(
                keyboard_row.text_markdown
            )
            await update.message.reply_photo(
                keyboard_row.send_picture,
                reply_markup=Keyboard.reply_keyboard
            )
UsersAdapterClass.keyboard_key_handler = keyboard_key_handler

async def proceed_registration_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid     = update.effective_chat.id
    user    = self.get(uid)
    state   = user.state
    save_as = user[Settings.user_document_name_field]
    registration_curr = Registration.get(state)
    registration_next = Registration.get_next(state)

    last_main_state = (state == Registration.last_main_state)
    last_state      = (state == Registration.last_state)

    state_val, save_to = self._prepare_state_to_save(update.message, registration_curr.document_link)
    if state_val == None:
        await update.message.reply_markdown(registration_curr.question, reply_markup=registration_curr.reply_keyboard)
        return

    if last_state:
        await update.message.reply_markdown(Settings.registration_pre_complete, reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_markdown(registration_next.question, reply_markup=registration_next.reply_keyboard)

    update_vals = {state: state_val}
    if last_main_state:
        update_vals['is_active'] = I18n.yes
    
    await self._batch_update_or_create_record(update.effective_chat.id, save_to=save_to, save_as=save_as, app=context.application,
        state = '' if last_state else registration_next.state,
        **update_vals
    )

    count = self.active_user_count()
    if last_main_state and self.should_send_report(count):
        Groups.send_to_all_admin_groups(
            context.application,
            Report.currently_active_users_template.format(count=count),
            ParseMode.MARKDOWN
        )
    
    if last_state:
        await asyncio.sleep(1)
        main_track_title, main_track, _, sub_track = await self.pre_load_tracks(uid)
        await update.message.reply_markdown(Settings.registration_complete)
        await update.message.reply_markdown(main_track)
        await update.message.reply_markdown(sub_track, reply_markup=Keyboard.get_reply_keyboard(main_track_title, I18n.track_state_main))
UsersAdapterClass.proceed_registration_handler = proceed_registration_handler

async def pre_load_tracks(self, uid: int|str) -> tuple[str,str,str,str]:
    main_track_title, main_track, sub_track_title, sub_track = np.array(await self.wks.batch_get([
        utils.rowcol_to_a1(self.wks_row(uid), Settings.user_main_track_title_collumn_num),
        utils.rowcol_to_a1(self.wks_row(uid), Settings.user_main_track_collumn_num),
        utils.rowcol_to_a1(self.wks_row(uid), Settings.user_sub_track_title_collumn_num),
        utils.rowcol_to_a1(self.wks_row(uid), Settings.user_sub_track_collumn_num),
    ])).flatten()
    Log.info(f"Got track for user with {uid=}: {main_track_title=} and {sub_track_title=}")
    self.as_df.loc[self.selector(uid), 'main_track_title'] = main_track_title
    self.as_df.loc[self.selector(uid), 'main_track']       = main_track
    self.as_df.loc[self.selector(uid), 'sub_track_title']  = sub_track_title
    self.as_df.loc[self.selector(uid), 'sub_track']        = sub_track
    return main_track_title, main_track, sub_track_title, sub_track
UsersAdapterClass.pre_load_tracks = pre_load_tracks

async def restart_help_on_registration_complete_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    template = Settings.user_template_from_update(update)
    main_track_title = self.get(update.effective_chat.id).main_track_title
    await update.message.reply_markdown(
        template.format(template = Settings.restart_on_registration_complete),
        reply_markup=Keyboard.get_reply_keyboard(main_track_title, I18n.track_state_main)
    )
UsersAdapterClass.restart_help_on_registration_complete_handler = restart_help_on_registration_complete_handler