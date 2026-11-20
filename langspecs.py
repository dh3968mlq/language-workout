import utils

def get_langspecs():
    langspecs = {
        "fr":{
            "table":"frenchwords",
            "language":"french",
            "colheading":"French word",
            "icon":"fxemoji:franceflag",
        },
        "es":{
            "table":"spanishwords",
            "language":"spanish",
            "colheading":"Spanish word",
            "icon":"fxemoji:spanishflag",
        },
        "it":{
            "table":"italianwords",
            "language":"italian",
            "colheading":"Italian word",
            "icon":"fxemoji:italianflag",
        },
        "jp":{
            "table":"japanesewords",
            "language":"japanese",
            "colheading":"Japanese word",
            "icon":"fxemoji:japanflag",
            "texthoverfunction":utils.jtranslate,
        },
    }
    return langspecs