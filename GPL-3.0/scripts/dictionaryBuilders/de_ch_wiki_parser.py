import os
import re
import math
import glob
import mwparserfromhell
from lxml import etree
from collections import Counter, defaultdict

# --- CONFIGURATION ---
MIN_WORD_COUNT = 500
MIN_BIGRAM_COUNT = 10
MAX_WORD_LEN = 48
WIKI_FILE = "alswiki-20260401-pages-articles.xml"
REPORT_FILE = "added_words.txt"

# 1. WHITELIST OF SHORT WORDS (de_CH / Alemannic)
# Only these 2- and 3-letter words are kept. Others (e.g. px, ra, id) will be removed.
WHITELIST_SHORT = {
    'vo', 'si', 'uf', 'im', 'de', 'am', 'us', 'as', 'es', 'um', 'mi', 'di', 'hi', 'zu', 'ja', 'so', 'du', 'er', 'sy',
    'und', 'die', 'der', 'das', 'het', 'nid', 'nit', 'mer', 'bis', 'ich', 'mir', 'für', 'fir', 'vun', 'bim', 'gha',
    'git', 'däm', 'häi', 'wil', 'nüt', 'ene', 'maa', 'hed', 'hüt', 'kei', 'zit', 'zyt', 'wia', 'gee', 'zom', 'nöd', 'won',
    'dem', 'den', 'des', 'ein', 'mal', 'man', 'nur', 'nun', 'ufm', 'usw', 'vom', 'von', 'vor', 'wär', 'wem', 'wen', 'wer',
    'wie', 'woh', 'zur', 'zue', 'drz', 'nei', 'nui', 'los', 'tuet', 'tue'
}

# 2. COMPREHENSIVE BLACKLIST (CODE, UI, ARTIFACTS)
TECHNICAL_BLACKLIST = {
    # Lua and MediaWiki scripting artifacts
    'then', 'elseif', 'function', 'true', 'false', 'return', 'local', 'and', 'not', 'or', 'end',
    'require', 'pcall', 'tostring', 'tonumber', 'invoke', 'module', 'args', 'util', 'error',
    'changes', 'mediawiki', 'template', 'references', 'noinclude', 'includeonly', 
    'onlyinclude', 'nowiki', 'gallery', 'math', 'formatnum', 'expr', 'switch', 'ifeq', 'ifexist',
    'ifexpr', 'assigned', 'failsafe', 'datavalue', 'itemid', 'property', 'snaktype', 'mainsnak',
    'qualifiers', 'pid', 'qid', 'entityid', 'imageid', 'qualifier', 'versioning', 'datetime',
    'retval', 'ndates', 'context', 'sampletext', 'tagopen', 'tagclose', 'notoc', 'picto',

    # UI and recent findings
    'admin', 'advanced', 'association', 'award', 'black', 'book', 'books', 'calendar', 'case',
    'centre', 'center', 'college', 'config', 'create', 'editing', 'entity', 'foundation', 'group', 
    'important', 'join', 'maps', 'message', 'music', 'next', 'number', 'please', 'posted', 'read', 
    'recent', 'records', 'sciences', 'society', 'space', 'state', 'subscribe', 'translate', 
    'unsubscribe', 'used', 'work', 'university', 'world', 'history', 'community', 'article',
    'visualeditor', 'translations', 'incubator', 'external', 'links', 'about', 'help', 'contact',
    'search', 'latest', 'available', 'using', 'details', 'summary', 'edit', 'results', 'result',
    'thank', 'easier', 'questions', 'comments', 'settings', 'options', 'default', 'defaults',
    
    # Other technical
    'https', 'http', 'www', 'wikimedia', 'wikipedia', 'wikisource', 'wikidata', 'nbsp', 'category',
    'file', 'image', 'thumb', 'srf', 'insee', 'id', 'jh', 'frz', 'aspx', 'htm', 'pdf', 'url', 'href', 'src',
    'px', 'em', 'rem', 'rgb', 'rgba', 'faffff', 'aaaaaa', 'fefefe', 'editbutton', 'mainpagetab',
    
    # Other junk
    'about','academy','académie','addclass','adjust','advice','affect','africa','african','again',
    'albedo','align','alliance','allium','ambassadors','america','american','ancien','ancient','another',
    'apply','approximant','arabic','architecture','archives','area','arts','assign','attempt','atlantique',
    'austria','autres','available','aviation','awards','aware','bachelor','based','because','been','before',
    'being','best','better','between','bgcolor','bible','biology','blue','board','bold','boolean','border',
    'born','both','britain','british','building','call','called','campaign','canal','century','challenge',
    'changed','channel','class','classname','classical','clear','collection','comedy','comme','comment',
    'committee','company','complete','complex','conference','content','contest','contribute','contributions',
    'control','copy','country','cours','creative','culture','current','cycling','death','decimal','default',
    'democratic','description','descriptions','development','dialektologie','dialects','dictionary','diff',
    'display','district','documentation','done','dream','during','each','early','earth','edit','edizioni',
    'education','egypt','elections','empty','encyclop','engl','error','evaluer','every','everyone','example',
    'externaldata','family','fantasy','february','feat','female','fetch','fiction','field','float','foreign',
    'found','frameless','freedom','full','gadget','game','games','gender','general','german','give','given',
    'gloss','gothic','government','greek','handbook','hard','head','heart','height','history','house','hour',
    'imagemap','including','india','instead','into','invalid','ireland','islamic','issue','issues','january',
    'jewish','king','know','label','labour','lake','language','late','lead','league','length','license','like',
    'links','lists','literature','location','longer','lower','make','making','margin','match','medieval',
    'metal','method','middle','might','minor','minutes','modalverb','month','mother','mountain','move',
    'movement','must','names','namespace','nations','navbox','navy','need','nice','night','node','north',
    'numbers','object','october','officinalis','only','options','organisatione','origin','other','over',
    'padding','pages','pairs','param','params','period','philosophy','physical','physics','place','plain',
    'policy','political','politics','possible','prepared','present','print','prize','process','properties',
    'proto','publications','publishing','random','recurrent','redirect','regnum','remove','removed','replace',
    'republic','request','results','retrieve','right','rights','river','role','round','rowspan','rural','sans',
    'scale','school','scientific','scripts','search','section','seek','self','serial','series','settings',
    'seven','shift','since','slam','smith','society','sociétè','source','sources','south','spec','species',
    'spoken','states','storage','strategy','stroke','structure','study','subsp','success','summary','suited',
    'switzerland','templates','than','thanks','theatre','theory','think','those','three','through','today',
    'toolbar','trek','ultimate','united','unknown','upload','upper','upright','uses','valign','village',
    'volume','volunteer','vulgaris','water','week','weight','while','width','wikitext','wiktionary','without',
    'women','working','world','writers','writing','year','years','your','already', 'append', 'bottom', 
    'cell', 'choice', 'colony', 'come', 'county', 
    'dialect', 'digits', 'discussion', 'document', 'does', 'errors', 'general', 
    'history', 'intercom', 'invert', 'languages', 'left', 'many', 'messages', 
    'movie', 'people', 'precondition', 'postcondition', 'prefix', 'race', 
    'room', 'sign', 'stop', 'survey', 'temp', 'trim', 'vertical', 'view',
    'aisne', 'campagne', 'conseil', 'commune', 'histoire', 'maison', 'musée', 
    'stade', 'territoire', 'variétés', 'vitalité', 'vous', 'agglo', 'allier', 
    'amiens', 'ardèche', 'ariège', 'auxerre', 'avignon', 'belfort', 'bourges', 
    'chaumont', 'clermont', 'cotentin', 'creuse', 'doubs', 'dreux', 'finistère', 
    'indre', 'isère', 'langres', 'lorient', 'marne', 'meuse', 'morbihan', 
    'morvan', 'nièvre', 'oloron', 'orléans', 'perpignan', 'pyrénées', 
    'quimper', 'sarthe', 'vannes', 'vaucluse', 'vienne', 'yonne', 'carex', 
    'historia', 'liber', 'officinalis', 'prunus', 'vulgaris', 'alswiki', 
    'cellspacing', 'commons', 'digitalisat', 'externaldata', 'indexof', 
    'innerhtml', 'ipairs', 'municipalities', 'phabricator', 'referanza', 
    'sitelink', 'template', 'templatedata', 'wikibase', 'wikicon', 
    'wikileaks', 'wikipedias', 'wikitable', 'dition', 'ndert', 'pinal', 
    'parms', 'perf', 'prät', 'rger', 'sche', 'tzer',
    'rahmenlos', 'size', 'weblingg', 'fuessnoote', 'fuessnote', 'websitta', 'ainzelnoohwiisa', 'houptsyte',
    'cklung', 'bevelkerungsentw', 'inwohnerinsee', 'teau', 'lothr', 'reschy', 'stro', 'webl', 'schè', 
    'schlie', 'terfili', 'stra', 'wwernumma', 'dits', 'teràtüür', 'ngisch', 'wwer', 'frànkr', 'ckelt', 
    'lich', 'prow', 'besan',
}

# 3. FOREIGN LANGUAGE STOPWORDS (French and English)
FOREIGN_STOPWORDS = {
    # French (administration/structure)
    'le', 'la', 'les', 'des', 'du', 'en', 'un', 'une', 'pour', 'avec', 'dans', 'et', 'il', 'elle', 'qui', 'que',
    'sur', 'plus', 'pas', 'aux', 'ce', 'cette', 'est', 'sont', 'ont', 'fait', 'pays', 'département', 'communauté', 
    'communes', 'arrondissement', 'canton', 'région', 'chef', 'lieu', 'code', 'recensement', 'logements', 
    'agglomération', 'métropole', 'université', 'historique', 'grand', 'ouest', 'vienne', 'bains', 'saint', 'sainte',
    'vallee', 'vallée', 'vallees', 'chateau', 'mont', 'monts', 'sud', 'nord', 'bourg', 'villages', 'commune', 'maire', 
    'mairie', 'francaise', 'français', 'française', 'depuis', 'terres', 'comminges', 'nouveau', 'anciens', 'ancienne', 
    'champagne', 'franche', 'valois', 'lieux',
    
    # English (stopwords)
    'the', 'of', 'and', 'in', 'to', 'for', 'by', 'on', 'with', 'as', 'at', 'from', 'this', 'that', 'it', 'is', 'an',
    'be', 'are', 'was', 'were', 'have', 'has', 'would', 'should', 'could', 'which', 'what', 'who', 'where', 'when',
    'why', 'there', 'their', 'they', 'we', 'us', 'our', 'he', 'she', 'him', 'her', 'his', 'hers', 'its', 'them', 'these',
    'soon', 'dear', 'side', 'more', 'some', 'studies', 'alsace', 'lons', 'noms', 'étymologique', 
    'langues', 'argonne', 'coteaux', 'villers', 'vosges', 'pernay', 'vallées', 'qamar'
}

def is_garbage(word):
    """Logic rejecting technical noise."""
    if len(word) <= 3 and word not in WHITELIST_SHORT:
        return True
    if any(char.isdigit() for char in word):
        return True
    if len(word) > 8 and (word.endswith('ae') or word.endswith('ii')):
        return True
    if not re.search(r'[aeiouyäöüàéè]', word):
        return True
    if bool(re.fullmatch(r'^(i|v|x|l|c|d|m)+$', word)):
        return True
    return False

def clean_wiki_text(raw_text):
    if not raw_text: return ""
    try:
        wikicode = mwparserfromhell.parse(raw_text)
        text = wikicode.strip_code()
    except:
        text = re.sub(r'\{\{.*?\}\}', '', raw_text, flags=re.DOTALL)
    text = str(text).replace('ß', 'ss').replace('ẞ', 'SS')
    text = re.sub(r'[^a-zA-ZäöüÄÖÜàéè]', ' ', text)
    return text.lower()

def scale_to_255(count, max_count):
    if count <= 0: return 0
    if max_count <= 1: return 255
    return max(1, min(255, int((math.log(count) / math.log(max_count)) * 255)))

def get_stats(wiki_path):
    print(f"--- STARTED SCANNING: {wiki_path} ---")
    word_counts = Counter()
    bigram_stats = defaultdict(Counter)
    
    context = etree.iterparse(wiki_path, events=('end',), tag='{*}text')
    
    count = 0
    for _, elem in context:
        text = clean_wiki_text(elem.text)
        tokens = text.split()
        
        filtered_tokens = []
        for word in tokens:
            if (word not in TECHNICAL_BLACKLIST and
                word not in FOREIGN_STOPWORDS and 
                not is_garbage(word)):
                filtered_tokens.append(word)
        
        for i in range(len(filtered_tokens)):
            w1 = filtered_tokens[i]
            word_counts[w1] += 1
            if i < len(filtered_tokens) - 1:
                w2 = filtered_tokens[i+1]
                if w1 != w2: 
                    bigram_stats[w1][w2] += 1
        
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
        
        count += 1
        if count % 100 == 0:
            print(f"Processed {count} articles...", end='\r', flush=True)

    print(f"\nSCAN COMPLETE. Total: {count} articles.\n")
    return word_counts, bigram_stats

def process():
    combined_files = glob.glob("*.combined")
    if not combined_files:
        print("Error: No .combined file found")
        return
    input_file = combined_files[0]
    raw_word_counts, bigram_results = get_stats(WIKI_FILE)
    print("Loading base dictionary...")
    final_dict = {}
    with open(input_file, 'r', encoding='utf-8') as f:
        header = f.readline()
        for line in f:
            if "word=" in line:
                try:
                    parts = dict(item.split("=") for item in line.strip().split(","))
                    final_dict[parts["word"].lower()] = int(parts["f"])
                except: continue
    added_report = []
    max_w_freq = max(raw_word_counts.values()) if raw_word_counts else 1
    for word, count in raw_word_counts.items():
        if count >= MIN_WORD_COUNT and word not in final_dict:
            f_val = scale_to_255(count, max_w_freq)
            final_dict[word] = f_val
            added_report.append((word, count))
    max_b_freq = 0
    for b_counts in bigram_results.values():
        if b_counts:
            # We search for the max only among those that meet the threshold
            for b_word, b_count in b_counts.items():
                if b_count >= MIN_BIGRAM_COUNT:
                    if b_count > max_b_freq: max_b_freq = b_count
    sorted_words = sorted(final_dict.items(), key=lambda x: x[1], reverse=True)
    output_file = input_file + '.grown'
    print(f"Saving: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f_out:
        f_out.write(header)
        for word, f_val in sorted_words:
            f_clamped = min(f_val, 255)
            f_out.write(f"word={word},f={f_clamped},flags=,originalFreq={f_clamped}\n")
            top_b = bigram_results[word].most_common(5) # Check top 5 to have a reserve after filtering
            written_bigrams = 0
            for nxt, b_freq_raw in top_b:
                if written_bigrams >= 3: break
                if nxt in final_dict and b_freq_raw >= MIN_BIGRAM_COUNT:
                    f_norm = scale_to_255(b_freq_raw, max_b_freq)
                    f_out.write(f"  bigram={nxt},f={f_norm}\n")
                    written_bigrams += 1
    added_report.sort(key=lambda x: x[1], reverse=True)
    words_only = [word for word, count in added_report]
    with open(REPORT_FILE, 'w', encoding='utf-8') as f_rep:
        f_rep.write(", ".join(words_only))
    print(f"DONE. Added {len(added_report)} new words. Report: {REPORT_FILE}")

if __name__ == "__main__":
    process()