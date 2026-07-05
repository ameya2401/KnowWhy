import re

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "arent", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "cant", "cannot", "could", "couldnt", "did", "didnt", "do", "does", "doesnt",
    "doing", "dont", "down", "during", "each", "few", "for", "from", "further", "had", "hadnt",
    "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes", "her", "here", "heres",
    "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "ill", "im", "ive", "if",
    "in", "into", "is", "isnt", "it", "its", "itself", "lets", "me", "more", "most", "mustnt", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shant", "she", "shed", "shell", "shes",
    "should", "shouldnt", "so", "some", "such", "than", "that", "thats", "the", "their", "theirs",
    "them", "themselves", "then", "there", "theres", "these", "they", "theyd", "theyll", "theyre",
    "theyve", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasnt", "we", "wed", "well", "were", "weve", "werent", "what", "whats", "when", "whens",
    "where", "wheres", "which", "while", "who", "whos", "whom", "why", "whys", "with", "wont",
    "would", "wouldnt", "you", "youd", "youll", "youre", "youve", "your", "yours", "yourself",
    "yourselves"
}

TECHNICAL_IDENTIFIERS = {
    "postgresql", "postgres", "jwt", "oauth", "fastapi", "react", "redis", "docker", "github",
    "notion", "alembic", "sqlalchemy", "python", "typescript", "sqlite", "git", "rest", "api"
}

class QueryProcessor:
    @classmethod
    def process(cls, query: str) -> dict:
        """
        Process user search query.
        Returns:
            {
                "raw_query": str,
                "normalized_query": str,
                "tokens": list[str],
                "phrases": list[str],
                "technical_terms": list[str]
            }
        """
        if not query:
            return {
                "raw_query": "",
                "normalized_query": "",
                "tokens": [],
                "phrases": [],
                "technical_terms": []
            }

        # Phrase detection: extract text inside double quotes
        phrases = re.findall(r'"([^"]+)"', query)
        
        # Clean query by removing quotes for tokenization
        clean_query = query.replace('"', ' ')
        
        # Lowercase and split into tokens
        raw_tokens = [t.strip().lower() for t in re.split(r'\s+', clean_query) if t.strip()]
        
        tokens = []
        technical_terms = []
        
        for token in raw_tokens:
            # Strip trailing/leading punctuation but keep internal dashes/underscores for technical words
            cleaned_token = re.sub(r'^[^\w\-\_]+|[^\w\-\_]+$', '', token)
            if not cleaned_token:
                continue
            
            # Check technical term preservation
            if cleaned_token in TECHNICAL_IDENTIFIERS or cleaned_token.replace("-", "") in TECHNICAL_IDENTIFIERS:
                technical_terms.append(cleaned_token)
                tokens.append(cleaned_token)
            elif cleaned_token not in STOP_WORDS:
                tokens.append(cleaned_token)

        normalized_query = " ".join(tokens)

        return {
            "raw_query": query,
            "normalized_query": normalized_query,
            "tokens": tokens,
            "phrases": [p.lower() for p in phrases],
            "technical_terms": technical_terms
        }
