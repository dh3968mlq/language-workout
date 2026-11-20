'''
Callback for layout_main_screen
PARENT OF:
    modal-find: 
        triggered by button-search.n_clicks
    vocab lists
        triggered by root-vl-button-lists.n_clicks   
'''
from typing import Any
from dash import Input, Output, State, no_update, ctx
import pandas as pd
import cb_main_processes
import utils

def cre_callbacks(app, engine, prefix, lspec, adminuser=False):

    table = lspec["table"]
    language=lspec["language"]
    texthoverfunction = lspec.get("texthoverfunction", None)

    # ------------------------------------------------------------------
    # -- Initial load callback
    # -- A separate callback, since the main callback has allow_duplicate=True
    @app.callback(
        Output(prefix+"root-button-get-foreign-word","n_clicks"), # -- trigger an initial word selection
        Output(prefix+"root-select-show-what", "data"),          
    )
    def initialise():
        # -- list of wordlists
        with engine.connect() as conn:
            sql = f"""select to_char(fwl_id, '99999') value, fwl_name label, count(1) n
                                from {language}wordlists, {language}wordinlist
                                where fwl_id = fwdl_fwl_id
                                group by fwl_id
                                order by fwl_name"""
            conn.rollback()   # speculative attempt to avoid occasional PendingRollbackError
            df = pd.read_sql(sql, conn)
    
        listlst = df.to_dict(orient="records")
        listlst = [{"value":x["value"],"label":x["label"] + f" ({x['n']})"} for x in listlst]
        whatdata=[{"value":"All", "label":"All"},
                  {"value":"Phrases", "label":"Phrases"}] + listlst
        return 0, whatdata
    # ------------------------------------------------------------------
    # -- Callback to deal with everything on main screen
    outputs = [
        ("root-chk-focus","checked"), ("root-chk-focus","label"), ("root-chk-noncore","checked"), 
        ("root-dictionary-lookup","href"), ("root-english-text", "value"), ("root-foreign-text", "children"),
        ("root-text-hovercarddropdown", "children"), ("root-text-notes", "value"), ("root-txt-corpusfreq","children"),
        ("root-store-focussed", "data"), ("root-store-selected-word", "data"),
        ("root-store-words", "data")
    ]
    inputs = [
        ("root-button-get-english","n_clicks"), ("root-button-get-foreign-word","n_clicks"), 
        ("root-button-gupload","n_clicks"), 
        ("root-chk-focus","checked"), ("root-chk-incnoncore","checked"), 
        ("root-select-nwords","value"), ("root-select-show-what","value"), 
        ("root-store-selected-word", "data")   # -- Can be triggered by Output from CHILD - Find Word
    ]
    states = [
        ("root-chk-noncore","checked"), ("root-english-text", "value"), ("root-text-notes", "value"),
        ("root-store-focussed", "data"), ("root-store-words", "data")
    ]

    callback_outputs = (Output(prefix+elid, elprop, allow_duplicate=True) for (elid, elprop) in outputs)
    callback_inputs = (Input(prefix+elid,elprop) for (elid, elprop) in inputs)
    callback_states = (State(prefix+elid,elprop) for (elid, elprop) in states)
    @app.callback(*callback_outputs, *callback_inputs, *callback_states, prevent_initial_call=True)
    def main_screen_callback(*args):
        dp, dr = utils.cb_collate(args, ltrim = len(prefix))
        trigger = ctx.triggered_id

        if dp["root-store-focussed.data"] is None:
             dp["root-store-focussed.data"] = []

        # -- updating database should be the first action
        if database_is_updated := (adminuser and (trigger == prefix+"root-button-gupload")):
            cb_main_processes.upload(
                dp["root-button-gupload.n_clicks"],
                dp["root-english-text.value"],
                dp["root-text-notes.value"],
                dp["root-store-selected-word.data"],
                dp["root-chk-focus.checked"],
                dp["root-chk-noncore.checked"],
                engine, adminuser, table
            )

        # -- user-mode click on root-chk-focus - update focus list
        if focus_updated := (trigger == prefix+"root-chk-focus" and not adminuser):
            wordid = dp["root-store-selected-word.data"]["fwd_id"]
            dr["root-store-focussed.data"] = dp["root-store-focussed.data"]

            if dp["root-chk-focus.checked"]:
                dr["root-store-focussed.data"].append(wordid)
            else:
                dr["root-store-focussed.data"].remove(wordid)
    
            dr["root-chk-focus.label"] = f"Focus ({len(dr['root-store-focussed.data'])})"
            dp["root-store-focussed.data"] = dr["root-store-focussed.data"]   # May be needed later

        # -- Populate word table if necessary
        if store_words_updated := (
            trigger in [prefix+"root-select-show-what",
                        prefix+"root-chk-incnoncore",
                        prefix+"root-select-nwords",
                        ] or
            focus_updated or
            database_is_updated or
            not dp["root-store-words.data"]
        ):
            dr["root-store-words.data"] = \
                utils.get_wordlist(
                    dp["root-select-nwords.value"], 
                    dp["root-select-show-what.value"], 
                    dp["root-chk-incnoncore.checked"], 
                    engine,
                    language=language,
                    focuslist=None if adminuser else dp["root-store-focussed.data"]
                )
            dr["root-chk-focus.label"] = f"Focus ({len(dr['root-store-words.data']['focussed'])})"
            dp["root-store-words.data"] = dr["root-store-words.data"]  # may be needed subsequently
            
        # -- select new word if necessary
        if trigger in [prefix+"root-button-get-foreign-word", prefix+"root-store-selected-word"] or \
                store_words_updated:
            dr["root-store-selected-word.data"] = \
                cb_main_processes.get_foreign_word(
                    dp["root-store-selected-word.data"],
                    dp["root-store-words.data"],
                    dp["root-store-focussed.data"],
                    engine, prefix, table, adminuser
                )
            
            # -- UI updates as consequence of picking new word
            d = dr["root-store-selected-word.data"]
            dr["root-foreign-text.children"] = d["fwd_word"]
            dr["root-text-hovercarddropdown.children"] = texthoverfunction(d["fwd_word"]) if texthoverfunction else no_update

            # -- Leave these fields blank if (a) they were blank already, or (b) the word has changed
            if (not dp["root-store-selected-word.data"] or \
                    d["fwd_word"] != dp["root-store-selected-word.data"]["fwd_word"]) or \
                    not dp["root-english-text.value"]:
                dr["root-english-text.value"] = ""
                dr["root-text-notes.value"] = ""
            else:
                dr["root-english-text.value"] = d["fwd_englishword"]
                dr["root-text-notes.value"] = d["fwd_notes"]

            dr["root-chk-focus.checked"] = d["fwd_focus"] if adminuser \
                    else (d["fwd_id"] in dp["root-store-focussed.data"])
            
            dr["root-chk-noncore.checked"] = d["fwd_noncore"]
            dr["root-txt-corpusfreq.children"] = f"Frequency: {d['fwd_frequency']}"
            dr["root-dictionary-lookup.href"] = f"https://jisho.org/search/{d['fwd_word']}" if prefix == "jp-" \
                else f"https://www.wordreference.com/{prefix[:-1]}en/{d['fwd_word']}"

        elif trigger == prefix+"root-button-get-english":
            def submissing(val, fill):
                return val if val else fill
            dr["root-english-text.value"] = submissing(dp["root-store-selected-word.data"]["fwd_englishword"], "<not known>")
            dr["root-text-notes.value"] = submissing(dp["root-store-selected-word.data"][f"fwd_notes"], "") 

        return utils.cb_results(dr)
