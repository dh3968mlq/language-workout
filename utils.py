import pandas as pd
import random
from typing import Any
from dash import ctx, no_update

def cre_wordlist_sql(nwords, show_what, incnoncore, 
                     focus, # "yes", "no", "both"
                     orderbyfreq, # bool
                     language="french",
                    filtertext="", engine=None,
                    focuslist=None, 
                    searchwithin=True, searchenglish=False):

    phrasesonly = (show_what == "Phrases")

    if focuslist is None:
        focusxpr = "fwd_focus"
    elif len(focuslist) == 0:
        focusxpr = "false"
    else:
        focusxpr = f"(fwd_id in ({','.join([str(f) for f in focuslist])}))"

    if focus == "yes":
        focusselector = f"and {focusxpr}"
    elif focus == "no":
        focusselector = f"and not {focusxpr}"
    elif focus == "both":
        focusselector = ""
    else:
        raise ValueError

    # -- filter expression
    fullfiltertext = ("%" if searchwithin else "") + filtertext + "%"
    searchcol = f"fwd_englishword" if searchenglish else "fwd_word" 
    filterxpn = f"and lower(unaccent({searchcol})) like lower(unaccent(%(filtertext)s))"

    phraseselector = f"""
    and (LENGTH(fwd_word)-LENGTH(REPLACE(fwd_word, ' ', '')) > 0 or
        position('phrase' in LOWER(REPLACE(fwd_notes, ' ', ''))) > 0  )
    """ if phrasesonly else ""

    coreselector = "" if incnoncore else f"""
    and not fwd_noncore
    """

    # -- select wordlist
    if show_what not in {"All", "Phrases"}:
        list_id = int(show_what)
        lsql = f"""
                    select fwdl_fwd_id id
                    from {language}wordinlist
                    where fwdl_fwl_id = {list_id}
            """
        if engine is None:
            raise ValueError("Engine is None")
        else:
            with engine.connect() as conn:
                df = pd.read_sql(lsql, conn)
                
        ids = [str(id) for id in df["id"]]
        sids = "(" + ",".join(ids) + ")"
        listselector = f"and fwd_id in {sids}" 
    else:
        listselector = ""

    ordering = f"order by  coalesce(fwd_frequency, 0) desc" if orderbyfreq \
        else f"order by  fwd_word"

    # '%' has to be doubled to be passed to psycopg2
    sql = f"""select fwd_id, fwd_word, fwd_englishword from {language}words
                where not fwd_ignore 
                {focusselector}
                and fwd_englishword is not null
                {filterxpn}
                {phraseselector}
                {coreselector}
                {listselector}
                {ordering} 
                limit {nwords if nwords>0 else "ALL"}
                """
    params  = {
        "filtertext":fullfiltertext
    }
    
    return sql, params

# -----------------------------------------------------------------------
def get_wordlist(nwords, show_what, incnoncore, engine, 
                 language="french",
                 filtertext="", focuslist=None):
    nwords =  -1 if nwords[0:3].upper() == "ALL" else int(nwords)
    with engine.connect() as conn:
        # focussed words
        sql, params = cre_wordlist_sql(-1, show_what, incnoncore, 
                     focus="yes", # "yes", "no", "both"
                     orderbyfreq=False,
                     language=language, engine=engine,
                     focuslist=focuslist)
        df_focussed = pd.read_sql(sql, conn, params=params)
        
        # unfocused words
        sql, params = cre_wordlist_sql(nwords, show_what, incnoncore, 
                     focus="no", # "yes", "no", "both"
                     orderbyfreq=True, 
                     language=language, engine=engine,
                     focuslist=focuslist)
        df_unfocussed = pd.read_sql(sql, conn, params=params)

        l_unfocussed = list(df_unfocussed[f"fwd_id"])
        l_focussed = list(df_focussed[f"fwd_id"])
        result = {
                    "focussed":l_focussed, 
                    "unfocussed":l_unfocussed,
                }

        return result
# --------------------------------------------------------------------------------------
def choose_selected_word(store_words, current_word_id=-1, store_focussed=[], adminuser=False):
    nfocusmax = 16  # -- Number of focussed words at which p_focussed reaches its maximum
    pfocusmax = 0.9 # -- max probability of picking a focussed word
    pfocusmin = 0.3 # -- min probability of picking a focussed word

    lfocussed = list(set(store_words["focussed"]) - {current_word_id})
    lunfocussed = list(set(store_words["unfocussed"]) - {current_word_id})

    nfocussed = len(lfocussed)
    ntotal = nfocussed + len(lunfocussed)

    focus_proportion = min(1.0, nfocussed / nfocusmax)
    p_focussed = pfocusmin * (1.0 - focus_proportion) + pfocusmax * focus_proportion

    # -- deal with unexpected case where all or almost all eligible words are focussed
    p_focussed = max(p_focussed, nfocussed/ntotal)

    rfilter = random.random()
    if rfilter <= p_focussed and nfocussed > 0:
        return random.choice(lfocussed) 
    else:
        return random.choice(lunfocussed)
# -------------------------------------------------------------------------
def cre_find_table_data(searchstr, engine,
                        language="french", colheading="French word",
                        searchwithin=True, searchenglish=False,
                        ):
    max_rows = 50
    sql, params = cre_wordlist_sql(max_rows + 1, show_what="All", incnoncore=True, 
                focus="both", # "yes", "no", "both"
                orderbyfreq=False, # bool
                language=language,
                filtertext=searchstr,
                searchwithin=searchwithin, searchenglish=searchenglish)

    if searchstr:
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn, params=params)    
            elements = df[["fwd_id","fwd_word", "fwd_englishword"]].\
                rename(columns={
                    "fwd_id":"id",
                    "fwd_word":colheading, 
                    "fwd_englishword":"English word"
                }).to_dict(orient="records")
            caption = f"1 word" if len(elements) == 1 else f"{len(elements)} words"
            if len(elements) > max_rows:
                elements = elements[0:max_rows]
                caption = f"First {max_rows} results displayed"
    else:
            elements = []
            caption = f"0 words"
   
    return elements, caption
# -------------------------------------------------------------------------------------
def cb_stripaddress(property):
    if "@" in property:
        return property[:property.find("@")]
    else:
        return property
# ----------------------------
def cb_collate(args, ltrim=0) -> tuple[dict[str, Any], dict[str, Any]]:
    'Create dicts of callback Inputs, States and Outputs'

    # -- dict of parameters (Inputs + States)
    plist = ctx.inputs_list + ctx.states_list
    assert len(plist) == len(args)
    dp = {p["id"][ltrim:] + "." + p["property"]:arg for p, arg in zip(plist, args)}

    # -- dict of results, initialised to no_update
    outputs = ctx.outputs_list
    if not outputs:
        dr = {}
    elif type(outputs) == dict:
        dr = {outputs["id"][ltrim:] + "." + cb_stripaddress(outputs["property"]):no_update}
    else:  # It should be a list
        dr = {r["id"][ltrim:] + "." + cb_stripaddress(r["property"]):no_update for r in outputs }
    return dp, dr
# ----------------------------
def cb_results(dr):
    'Create result to return from a callback'
    # -- dr should retain its initial ordering, and should not have acquired extra items
    if len(dr) == 0:
        assert(len(ctx.outputs_list)  == 0)
        return None
    elif len(dr) == 1:
        assert(type(ctx.outputs_list) == dict)
        return list(dr.values())[0]
    else:
        assert(len(dr) == len(ctx.outputs_list))
        return list(dr.values())
# ----------------------------------------------------------------------------------
# Conversion of Japanese kana (Hiragana and Katakana) to romaji (latin) characters
# Note: all digraphs here are written with a small ya/yu/yo
# So this won't treat a standard size ya/yu/yo as part of a digraph
d_hiragana_latin = {
    # Monographs
    'あ':'a', 'い':'i', 'う':'u', 'え':'e', 'お':'o',
    'か':'ka', 'き':'ki', 'く':'ku', 'け':'ke', 'こ':'ko',
    'さ':'sa', 'し':'shi', 'す':'su', 'せ':'se', 'そ':'so',
    'た':'ta', 'ち':'chi', 'つ':'tsu', 'て':'te', 'と':'to',
    'な':'na', 'に':'ni', 'ぬ':'nu', 'ね':'ne', 'の':'no',
    'は':'ha', 'ひ':'hi', 'ふ':'fu', 'へ':'he', 'ほ':'ho',
    'ま':'ma', 'み':'mi', 'む':'mu', 'め':'me', 'も':'mo',
    'や':'ya', 'ゆ':'yu', 'よ':'yo',
    'ら':'ra', 'り':'ri', 'る':'ru', 'れ':'re', 'ろ':'ro',
    'わ':'wa', 'を':'wo', 'ん':'n',
    # Digraphs
    'きゃ':'kya', 'きゅ':'kyu', 'きょ':'kyo',
    'しゃ':'sha', 'しゅ':'shu', 'しょ':'sho',
    'ちゃ':'cha', 'ちゅ':'chu', 'ちょ':'cho',
    'にゃ':'nya', 'にゅ':'nyu', 'にょ':'nyo',
    'ひゃ':'hya', 'ひゅ':'hyu', 'ひょ':'hyo',
    'みゃ':'mya', 'みゅ':'myu', 'みょ':'myo',
    'りゃ':'rya', 'りゅ':'ryu', 'りょ':'ryo', 
    # Monographs with diacritics
    'が':'ga', 'ぎ':'gi', 'ぐ':'gu', 'げ':'ge', 'ご':'go', 
    'ざ':'za', 'じ':'ji', 'ず':'zu', 'ぜ':'ze', 'ぞ':'zo', 
    'だ':'da', 'ぢ':'ji', 'づ':'zu', 'で':'de', 'ど':'do', 
    'ば':'ba', 'び':'bi', 'ぶ':'bu', 'べ':'be', 'ぼ':'bo', 
    'ぱ':'pa', 'ぴ':'pi', 'ぷ':'pu', 'ぺ':'pe', 'ぽ':'po',    
    # Digraphs with diacritics
    'ぎゃ':'gya', 'ぎゅ':'gyu', 'ぎょ':'gyo', 
    'じゃ':'ja', 'じゅ':'ju', 'じょ':'jo', 
    'ぢゃ':'ja', 'ぢゅ':'ju', 'ぢょ':'jo', 
    'びゃ':'bya', 'びゅ':'byu', 'びょ':'byo', 
    'ぴゃ':'pya', 'ぴゅ':'pyu', 'ぴょ':'pyo', 

}
# ----------------------------------------------------------------------------------
d_katakana_latin = {
    # Monographs
    'ア':'a', 'イ':'i', 'ウ':'u', 'エ':'e', 'オ':'o',
    'カ':'ka', 'キ':'ki', 'ク':'ku', 'ケ':'ke', 'コ':'ko',
    'サ':'sa', 'シ':'shi', 'ス':'su', 'セ':'se', 'ソ':'so',
    'タ':'ta', 'チ':'chi', 'ツ':'tsu', 'テ':'te', 'ト':'to',
    'ナ':'na', 'ニ':'ni', 'ヌ':'nu', 'ネ':'ne', 'ノ':'no',
    'ハ':'ha', 'ヒ':'hi', 'フ':'fu', 'ヘ':'he', 'ホ':'ho',
    'マ':'ma', 'ミ':'mi', 'ム':'mu', 'メ':'me', 'モ':'mo',
    'ヤ':'ya', 'ユ':'yu', 'ヨ':'yo',
    'ラ':'ra', 'リ':'ri', 'ル':'ru', 'レ':'re', 'ロ':'ro',
    'ワ':'wa', 'ヲ':'wo', 'ン':'n',
    # Digraphs
    'キャ':'kya', 'キュ':'kyu', 'キョ':'kyo',
    'シャ':'sha', 'シュ':'shu', 'ショ':'sho',
    'チャ':'cha', 'チュ':'chu', 'チョ':'cho',
    'ニャ':'nya', 'ニュ':'nyu', 'ニョ':'nyo',
    'ヒャ':'hya', 'ヒィ':'hyu', 'ヒョ':'hyo',
    'ミャ':'mya', 'ミュ':'myu', 'ミョ':'myo',
    'リャ':'rya', 'リュ':'ryu', 'リョ':'ryo', 
    # Monographs with diacritics
    'ガ':'ga', 'ギ':'gi', 'グ':'gu', 'ゲ':'ge', 'ゴ':'go', 
    'ザ':'za', 'ジ':'ji', 'ズ':'zu', 'ゼ':'ze', 'ゾ':'zo', 
    'ダ':'da', 'ジ':'ji', 'ズ':'zu', 'デ':'de', 'ド':'do', 
    'バ':'ba', 'ビ':'bi', 'ブ':'bu', 'ベ':'be', 'ボ':'bo', 
    'パ':'pa', 'ピ':'pi', 'プ':'pu', 'ペ':'pe', 'ポ':'po',    
    # Digraphs with diacritics
    'ギャ':'gya', 'ギュ':'gyu', 'ギョ':'gyo', 
    'ジャ':'ja', 'ジュ':'ju', 'ジョ':'jo', 
    'ヂャ':'ja', 'ヂュ':'ju', 'ヂョ':'jo', 
    'ビャ':'bya', 'ビュ':'byu', 'ビョ':'byo', 
    'ピャ':'pya', 'ピュ':'pyu', 'ピョ':'pyo', 

}
# -------------------------------------------------------------------
d_kana_latin = d_hiragana_latin.copy()
d_kana_latin.update(d_katakana_latin)
# -------------------------------------------------------------------
def jtranslate(jscript):
    th, _ = kanatranslate(jscript, d_kana_latin)
    return th
# -------------------------------------------------------------------
def kanatranslate(hiragana, d_kana_latin=d_kana_latin):
    hlen = len(hiragana)
    results = []
    charpos = 0
    ntranslated = 0
    tsupending = False    # If we encounter a small tsu, it doubles the next consonant. This indicates if we have just found one
    while charpos < hlen:
        char1 = hiragana[charpos]
        if charpos >= hlen - 1:    # processing the last character, must be monograph
            latin = str(d_kana_latin.get(char1, char1))
            if tsupending:
                latin = f"{latin[0]}{latin}"
            results.append(latin)
            charpos += 1
            ntranslated+= int(latin != char1)
        else:
            char2 = hiragana[charpos:charpos + 2]   # possible digraph
            latin2 = d_kana_latin.get(char2, None)
            if latin2:    # It's a digraph
                if tsupending:
                    latin2 = f"{latin2[0]}{latin2}"
                results.append(latin2)
                charpos +=2
                ntranslated+= 1
                tsupending = False
            elif char1 in {'っ','ッ'}:    # The small tsu character, doubling the next consonant
                tsupending = True
                charpos += 1
            elif char1 == 'ー':          # choonpu (Katakana), doubles the last vowel
                if results:
                    results.append(results[-1][-1])
                charpos += 1
                ntranslated+= 1
            else:     # Monograph
                latin = str(d_kana_latin.get(char1, char1))
                ntranslated+= int(latin != char1)
                if tsupending:
                    latin = f"{latin[0]}{latin}"
                results.append(latin)
                charpos += 1
                tsupending = False

    result = ' '.join(results)
    return result, ntranslated

