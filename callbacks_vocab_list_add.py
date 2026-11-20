'''
Callbacks for the vocab list add modal
CHILD OF:
    vocab lists (vl)
'''
from typing import Any
from dash import Input, Output, State, ctx
import pandas as pd
import utils

def cre_callbacks(app, engine, prefix, lspec, adminuser=False):
    language=lspec["language"]

    outputs = [
        ("vl-modal", "opened"), ("vl-select-list", "data"),  # PARENT outputs
        ("vla-modal", "opened"), ("vla-btn-ok", "disabled"),
        ("vla-alert-listname-blank","hide"), ("vla-alert-insert-failed","hide"),
    ]
    inputs = [
        ("vl-vla-button-add-list","n_clicks"), # PARENT trigger, in the vla functional group
        ("vla-modal", "opened"), ("vla-new-list", "value"),
        ("vla-btn-cancel","n_clicks"), ("vla-btn-ok","n_clicks")
    ]
    states = []

    callback_outputs = (Output(prefix+elid, elprop, allow_duplicate=True) for (elid, elprop) in outputs)
    callback_inputs = (Input(prefix+elid,elprop) for (elid, elprop) in inputs)
    callback_states = (State(prefix+elid,elprop) for (elid, elprop) in states)
    @app.callback(*callback_outputs, *callback_inputs, *callback_states, prevent_initial_call=True)
    def find_word_callback(*args):
        dp, dr = utils.cb_collate(args, ltrim = len(prefix))
        trigger = ctx.triggered_id
        fulltrigger = ctx.triggered[0]["prop_id"]

        if trigger == prefix+"vl-vla-button-add-list": # PARENT trigger
            dr["vla-modal.opened"] = True
            dr["vl-modal.opened"] = False

        elif fulltrigger == prefix+"vla-modal.opened":
            if not dp["vla-modal.opened"]: # only take action on close
                dr["vl-modal.opened"] = True   # PARENT output

        elif trigger == prefix+"vla-btn-cancel":
            dr["vla-modal.opened"] = False
            dr["vl-modal.opened"] = True   # PARENT output

        elif fulltrigger == prefix+"vla-btn-ok.n_clicks":
            listname = dp["vla-new-list.value"]
            if not listname:
                dr["vla-alert-listname-blank.hide"] = False
                dr["vla-alert-insert-failed.hide"] = True
            else:
                with engine.connect() as conn:
                    df = pd.DataFrame([{"fwl_name":listname}])
                    try:
                        df.to_sql(language+"wordlists", conn, if_exists="append", index=False)

                        df = pd.read_sql(
                            f"""select to_char(fwl_id, '99999') value, fwl_name label 
                                from {language}wordlists 
                                order by fwl_name""", 
                            conn
                        )
                        seldata = df.to_dict(orient="records")
                        dr["vla-modal.opened"] = False
                        dr["vla-alert-listname-blank.hide"] = False
                        dr["vla-alert-insert-failed.hide"] = True
                        dr["vl-select-list.data"] = seldata
                    except:
                        dr["vla-modal.opened"] = True
                        dr["vla-alert-listname-blank.hide"] = True
                        dr["vla-alert-insert-failed.hide"] = False

        elif fulltrigger == prefix+"vla-new-list.value":
            validname = bool(dp["vla-new-list.value"])
            dr["vla-alert-listname-blank.hide"] = validname
            dr["vla-btn-ok.disabled"] = not validname

        return utils.cb_results(dr)
