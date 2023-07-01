from spreadsheetbot.sheets.keyboard import KeyboardAdapterClass

from spreadsheetbot.sheets.i18n import I18n

from telegram import ReplyKeyboardMarkup

KeyboardAdapterClass.default_pre_async_init = KeyboardAdapterClass._pre_async_init
async def _pre_async_init(self):
    await self.default_pre_async_init()
    self.RERUN_TEST = I18n.rerun_test
KeyboardAdapterClass._pre_async_init = _pre_async_init

def get_key(self, col_name: str, value: str|int) -> str:
    return self._get(self.as_df[col_name] == value).key
KeyboardAdapterClass.get_key = get_key

def get_all_keys_by_track(self, track: str) -> list[str]:
    return self.as_df.loc[self.as_df.track == track].key.to_list()
KeyboardAdapterClass.get_all_keys_by_track = get_all_keys_by_track

def get_reply_keyboard(self, track: str, track_state: str) -> ReplyKeyboardMarkup:
    keys = self.get_all_keys_by_track(track)
    return ReplyKeyboardMarkup([
        keys[idx:idx+2]
        for idx in range(0,len(keys),2)
    ] + [
        [self.get_key('function', self.REGISTER_FUNCTION), self.get_key('function', self.RERUN_TEST)],
        [self.get_key('track_state', track_state)]
    ])
KeyboardAdapterClass.get_reply_keyboard = get_reply_keyboard

KeyboardAdapterClass.default_process_df_update = KeyboardAdapterClass._process_df_update
async def _process_df_update(self):
    await self.default_process_df_update()
    self.reply_keyboard = None
KeyboardAdapterClass._process_df_update = _process_df_update