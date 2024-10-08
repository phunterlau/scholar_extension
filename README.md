# Google Scholar Summarizer
A Chrome/Edge extension to summarize Google Scholar page. It has an overall summary on top of the page, plus a whole text summary next to each search result.

High voltage warning: it is mostly for my personal use, never promised stability or production quality, nor easy setups. Contributions on a better frontend is always welcomed and appreciated!

Change logs:

* Aug 10: added token display; added keywords per suggested questions; added concept highlights for further search and obsidian markdown support of knowledge graph; added more error handing from non-crawl content; refinded overall display box style for fold and unfold.
* Aug 2: added link cache expiration; started JSON mode for mindmap, followup research questions, suggsted search keywords
* Aug 1: added token auth, refactorized backend.
* July 31 afternoon: added long term cache for search results; added "Download Summary" function to export to Markdown; Add red panda animation next to the search button to start summary.
* July 31: update UI with a small blue line for progress bar under the search box; add red panda logo and user click the extension button to run summarization; add rate limiting to the backend.
* July 30: add Llama 3.1 support via Groq; add "start summary" and a progress bar, and the summary shows up one by one when done.

## How to install

1. Download the repo and unpack it.
2. Add your OpenAI API key or Groq API key for Llama
    - `export OPENAI_API_KEY=sk-...`
    - (optional) `export GROQ_API_KEY=gsk_...` (check `app.py` how to switch to Llama models)
    - (optional) `export JENA_READER_API_KEY=jina_` (check <https://jina.ai/reader/> for API use)
3. Add token secret `export JWT_SECRET=...`
4. Install Chrome extension in dev mode
    - Open Chrome and navigate to chrome://extensions/.
    - Enable "Developer mode" using the toggle in the top right corner.
    - Click on the "Load unpacked" button.
    - Select the "GoogleScholarSummarizer" folder where you extracted the extension files.
5. Enable the python backend
    - `pip install -r requirements.txt`
    - `cd GoogleScholarSummarizer/`
    - `python app.py`

## How to use

After successful installation and the backend is running, one can a scholarly red panda icon on a google scholar search page. Click it, see a nodding red panda animation, and wait for a few seconds for the progress bar finishing, one should see the summaries on the page.

The terminal window running the python backend should see the details, if concerned.

## How does it work

It has a JS frontend and a python/flask backend. The JS frontend load the google scholar search page for its query and the list of search result. The python backend crawls each link, summarize with `gpt-4o-mini` and the whole page. After that, the JS frontend re-render the page and insert the result to the page top and next to each result. The page should look like this and the summaries are in blue boxes:

<image src="screenshots/scholar-extension.jpg" width="800">

## Future work

Well, we definitely need a JS expert for a better frontend and UI. The backend can be replaced by a JS backend as well, since it is just on-demand crawling plus OpenAI API calls. In future, it is possible to use on-device LLM provided by Chrome or MLC WebLLM.

Another direction that I am working on: the flask backend can be powerful to collect external data beyond JS. Stay tuned.

## Acknowledgement  

* Jena.ai has a great reader function to crawl a webpage. Good job!
