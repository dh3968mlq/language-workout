from dash import no_update, ctx
from sqlalchemy import text
import pandas as pd
import utils

# ------------------------------------------------------------------------------
# "Get <foreign> word" button, or change to store_selected_word
def get_foreign_word(
        store_selected_word, 
        store_words, 
        store_focussed,
        engine, prefix="fr-", table="frenchwords",
        adminuser=False
    ):
    trigger = ctx.triggered_id

    if store_focussed is None:
        store_focussed = []

    # -- Pick new word if necessary
    if not store_selected_word:    # No current selected word, we must pick one
        word_id = utils.choose_selected_word(store_words, store_focussed=store_focussed, adminuser=adminuser)

    # -- Always accept a choice that comes through a change to store-selected-word
    elif trigger == prefix+"root-store-selected-word":
        word_id = store_selected_word["fwd_id"]

    # -- Otherwise pick a new word (a) on get foreign word button or (b) current selection not valid
    elif trigger == prefix+"root-button-get-foreign-word" or \
                    (store_selected_word["fwd_id"] not in store_words["focussed"] + store_words["unfocussed"]):
        word_id = utils.choose_selected_word(store_words, store_selected_word["fwd_id"], 
                                                store_focussed=store_focussed, adminuser=adminuser)
        
    else:     # All other cases keep current word
        word_id = store_selected_word["fwd_id"]

    # -- Get word details (always - in admin mode store_selected_word can be out of sync with the database)
    with engine.connect() as conn:
        sql = f"select * from {table} where fwd_id={word_id}"
        df = pd.read_sql(sql, conn)
        d_selected_word = df.to_dict(orient="records")[0]
        
    return d_selected_word
# ---------------------------------------------
# -- Upload changes to database
def upload(_, englishtext, notes, dword, chk_focus, chk_noncore,
           engine, adminuser=False, table="frenchwords"):

    if not adminuser:
        return

    # ---- define worker function
    def update_field(foreignword, field, value):
        foreignwordq = foreignword.replace("'","''") # Double up singlequotes for SQL

        if type(value) == str:
            valq = value.replace("'","''") if value else ""     # Double up singlequotes for SQL
            sql = f"update {table} set {field}='{valq}' where fwd_word='{foreignwordq}'"
        elif type(value) == bool:
            sql = f"update {table} set {field}={'true' if value else 'false'} where fwd_word='{foreignwordq}'"
        else:
            raise TypeError
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
    # --- end of def of update_field

    if (foreignword := dword['fwd_word']):
        if englishtext and englishtext != "<not known>":   # Only upload translation if there is one
            update_field(foreignword, f"fwd_englishword", englishtext)
            dword.update({f"fwd_englishword":englishtext})
        if notes:  # Only upload notes if there are some
            update_field(foreignword, f"fwd_notes", notes)
            dword.update({f"fwd_notes":notes})
        update_field(foreignword, f"fwd_focus", chk_focus)
        update_field(foreignword, f"fwd_noncore", chk_noncore)

    return
    