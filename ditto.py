# Keypirinha | A semantic launcher for Windows | http://keypirinha.com

import keypirinha as kp
import keypirinha_util as kpu
import sqlite3
import datetime

class Clip():
    def __init__(self, text, date, order):
        self.text = str(text)
        self.date = date
        self.order = int(order)

class Ditto(kp.Plugin):
    """Copy text from the Ditto Clipboard Manager back to the system clipboard."""
    
    # Constants
    DEFAULT_DATABASE_FILE = None
    DEFAULT_ITEM_LABEL = "Ditto"
    DEFAULT_ITEM_DESC = "Copy text from clipboard history to the system clipboard"
    DEFAULT_ALWAYS_SUGGEST = False
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_ITEM_LIMIT = 30
    KEYWORD = "ditto"
    
    # Variables
    database_file = DEFAULT_DATABASE_FILE
    item_label = DEFAULT_ITEM_LABEL
    always_suggest = DEFAULT_ALWAYS_SUGGEST
    date_format = DEFAULT_DATE_FORMAT
    item_limit = DEFAULT_ITEM_LIMIT
    
    def __init__(self):
        super().__init__()
        #self._debug = False # enables self.dbg() output
        self.dbg("CONSTRUCTOR")

    def on_start(self):
        self.dbg("On Start")
        self._read_config()

    def on_catalog(self):
        self.dbg("On Catalog")
        self.set_catalog([self._create_keyword_item(label=self.item_label + "...",short_desc=self.DEFAULT_ITEM_DESC)])

    def on_suggest(self, user_input, items_chain):
        self.dbg('On Suggest "{}" (items_chain[{}])'.format(user_input, len(items_chain)))
        if not items_chain and (not self.always_suggest or len(user_input) == 0):
            return

        if items_chain and (
                items_chain[0].category() != kp.ItemCategory.KEYWORD or
                items_chain[0].target() != self.KEYWORD):
            return

        suggestions = []
        clips = self._list_clips()
        if not clips == None and not len(clips) == 0:
            for c in clips:
                suggestions.append(self._create_expression_item(c.date, "", c.text))

        if len(suggestions) > 0:
            self.set_suggestions(suggestions, kp.Match.DEFAULT, kp.Sort.NONE)

    def on_execute(self, item, action):
        self.dbg('On Execute "{}" (action: {})'.format(item, action))
        if item and item.category() == kp.ItemCategory.EXPRESSION:
            kpu.set_clipboard(item.data_bag())

    def on_events(self, flags):
        self.dbg("On event(s) (flags {:#x})".format(flags))
        if flags & kp.Events.PACKCONFIG:
            self._read_config()
            self.on_catalog()
        
    def _read_config(self):
        settings = self.load_settings()
        self.database_file = settings.get_stripped("database_file", "main", self.DEFAULT_DATABASE_FILE)
        self.item_label = settings.get_stripped("item_label", "main", self.DEFAULT_ITEM_LABEL)
        self.always_suggest = settings.get_bool("always_suggest", "main", self.DEFAULT_ALWAYS_SUGGEST)
        self.date_format = settings.get_stripped("date_format", "main", self.DEFAULT_DATE_FORMAT)
        self.item_limit = settings.get_bool("item_limit", "main", self.DEFAULT_ITEM_LIMIT)
        
    def _create_keyword_item(self, label, short_desc):
        return self.create_item(
            category=kp.ItemCategory.KEYWORD,
            label=label,
            short_desc=short_desc,
            target=self.KEYWORD,
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.NOARGS
            )
    
    def _create_expression_item(self, label, short_desc, data_bag):
        return self.create_item(
            category=kp.ItemCategory.EXPRESSION,
            label="{}: {}".format(self.item_label, data_bag),
            short_desc="{} (Press Enter to copy the result)".format(label),
            target=str(label),
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE,
            data_bag=str(data_bag)
            )   
    
    def _list_clips(self):
        try:
            connection = sqlite3.connect(self.database_file)
            p = (self.item_limit,)
            c = connection.cursor()
            c.execute('SELECT * FROM Main ORDER BY clipOrder DESC LIMIT ?', p)
            self.dbg("Successfully loaded and read database file: " + self.database_file)
        except:
            self.info("Unable to load database file: " + str(self.database_file))
            return

        clips = []
        for row in c.fetchall():
            text = row[2]
            date = datetime.datetime.fromtimestamp(int(row[1])).strftime(self.date_format)
            order = row[9]
            clips.append(Clip(text, date, order))
        
        return clips