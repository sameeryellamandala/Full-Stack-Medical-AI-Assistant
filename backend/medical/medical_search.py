import urllib.request
import urllib.parse
import json
from typing import List, Dict


def _search_wikipedia(query: str, num_results: int = 3) -> List[Dict]:
    """
    Search Wikipedia using its free API (no API key needed).
    Returns article summaries relevant to the query.
    """
    results = []
    try:
        # Step 1: Search for matching articles
        search_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": str(num_results),
            "format": "json",
            "utf8": "1"
        })
        
        req = urllib.request.Request(search_url, headers={"User-Agent": "MedAIAssistant/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        search_results = data.get("query", {}).get("search", [])
        
        # Step 2: Get summaries for each result
        for item in search_results:
            title = item["title"]
            try:
                summary_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title)
                req = urllib.request.Request(summary_url, headers={"User-Agent": "MedAIAssistant/1.0"})
                with urllib.request.urlopen(req, timeout=8) as response:
                    summary_data = json.loads(response.read().decode())
                
                extract = summary_data.get("extract", "")
                if extract and len(extract) > 50:
                    results.append({
                        "title": title,
                        "organization": "Wikipedia",
                        "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}"),
                        "passage": extract[:1500],  # Cap at 1500 chars
                        "source_type": "Encyclopedia"
                    })
            except Exception as e:
                print(f"    Wikipedia summary error for '{title}': {e}")
                continue
                
    except Exception as e:
        print(f"    Wikipedia search error: {e}")
    
    return results


def _search_duckduckgo(query: str, num_results: int = 3) -> List[Dict]:
    """
    Search DuckDuckGo Instant Answer API (free, no API key needed).
    Returns relevant text snippets.
    """
    results = []
    try:
        search_url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        })
        
        req = urllib.request.Request(search_url, headers={"User-Agent": "MedAIAssistant/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        # Abstract (main result)
        abstract = data.get("AbstractText", "")
        abstract_source = data.get("AbstractSource", "DuckDuckGo")
        abstract_url = data.get("AbstractURL", "")
        if abstract and len(abstract) > 50:
            results.append({
                "title": data.get("Heading", query),
                "organization": abstract_source,
                "url": abstract_url,
                "passage": abstract[:1500],
                "source_type": "Web Search"
            })
        
        # Related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and "Text" in topic:
                text = topic.get("Text", "")
                if text and len(text) > 30:
                    results.append({
                        "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " ") if topic.get("FirstURL") else "Related Topic",
                        "organization": "DuckDuckGo",
                        "url": topic.get("FirstURL", ""),
                        "passage": text[:800],
                        "source_type": "Web Search"
                    })
                    
    except Exception as e:
        print(f"    DuckDuckGo search error: {e}")
    
    return results


def search_medical_knowledge(query: str) -> List[Dict]:
    """
    Search trusted sources for general medical knowledge.
    Uses Wikipedia API + DuckDuckGo Instant Answer API (both free, no API key needed).
    Falls back gracefully if either fails.
    """
    print(f"  [External Search] Querying Wikipedia + DuckDuckGo for: '{query}'")
    
    all_results = []
    
    # Search Wikipedia (primary - most detailed)
    wiki_results = _search_wikipedia(query + " medicine health", num_results=3)
    all_results.extend(wiki_results)
    print(f"  [Wikipedia] Found {len(wiki_results)} results")
    
    # Search DuckDuckGo (secondary - broader coverage)
    ddg_results = _search_duckduckgo(query, num_results=2)
    all_results.extend(ddg_results)
    print(f"  [DuckDuckGo] Found {len(ddg_results)} results")
    
    # If we got nothing from either, return a helpful fallback
    if not all_results:
        print(f"  [External Search] No results found, using LLM knowledge fallback")
        return [{
            "title": "No External Sources Found",
            "organization": "AI Knowledge Base",
            "url": "",
            "passage": f"No specific external sources were found for '{query}'. Please use your general medical knowledge to provide a comprehensive, accurate answer to the user's question. Structure the answer with clear sections, specific examples, and actionable advice.",
            "source_type": "Fallback"
        }]
    
    return all_results
