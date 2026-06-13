import re
from collections import Counter

# Hardcoded list of standard English stopwords to avoid NLTK dependency
STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", 
    "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", 
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", 
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", 
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", 
    "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", 
    "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", 
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", 
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", 
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", 
    "please", "could", "would", "tell", "explain", "give", "provide", "show", "help",
    "need", "want", "like", "make", "create", "write"
}

def generate_title(text: str) -> str:
    """
    Generates a 3-5 word chat title from text using zero external dependencies.
    Filters out common stopwords and picks the most frequent/meaningful remaining words.
    """
    if not text:
        return "New Chat"

    # 1. Lowercase and extract alphanumeric words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

    # 2. Filter out stop words
    filtered_words = [w for w in words if w not in STOP_WORDS]

    # If everything was filtered out, fallback to the original first few words
    if not filtered_words:
        fallback = [w for w in words if len(w) > 1]
        return " ".join(fallback[:3]).title() if fallback else "New Chat"

    # 3. Frequency scoring (most common words first)
    # If the text is short, frequency won't matter much, it will just keep the order
    # To keep the order natural for short sentences, we can use a stable frequency sort
    
    # We want to maintain original sentence order as much as possible for readability, 
    # but prioritize words that appear multiple times if it's a long prompt.
    word_counts = Counter(filtered_words)
    
    # Sort by frequency (desc), then by order of appearance
    seen = set()
    ordered_keywords = []
    for w in filtered_words:
        if w not in seen:
            seen.add(w)
            ordered_keywords.append(w)
            
    ordered_keywords.sort(key=lambda x: word_counts[x], reverse=True)

    # 4. Take top 4 words, then re-sort them back into their original sentence order for readability
    top_words = ordered_keywords[:4]
    
    final_title_words = [w for w in filtered_words if w in top_words]
    
    # Remove duplicates from final title while preserving sentence order
    final_clean = []
    for w in final_title_words:
        if w not in final_clean:
            final_clean.append(w)

    return " ".join(final_clean).title()
