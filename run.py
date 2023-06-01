import os
import pathlib
import urllib
import csv
import time

import download


OUTPUT = os.path.join(pathlib.Path(__file__).parent.resolve(), "output")


def page(request: Request, content: str) -> str:
    if request.headers.get("hx-boosted"):
        return content
    return f'''
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title id="title">youtube mp3</title>
            <link rel="icon" href="/static/smile.ico">
            <link rel="stylesheet" href="/static/pure-min.css">
            <link rel="stylesheet" href="/static/grids-responsive-min.css">
            <script src="/static/htmx.min.js"></script>
        </head>
        <style>
            body>main{{max-width:60em;margin:0 auto}}
            article{{margin:1em 0;border:thin solid lightgray;max-width:
            90%;box-shadow:0 3px 8px 2px rgba(0,0,0,0.1);}}
            article>header{{font-weight:bold;font-size:1.5em;padding:0.5rem;
            background:lightgray}}article>main{{padding:0.5rem}}
        </style>
        <body>
            {content}
        </body>
    </html>
    '''


async def index(request: Request):
    url = "https://www.youtube.com/watch?v=9bZkp7q19f0"
    guide = f'''
    <h1>Guide</h1>
    <article>
        <header>1. Get the video's URL</header>
        <main>
            <img class="pure-img" src="/static/url.png">
        </main>
    </article>
    <article>
        <header>2. Copy-paste the URL</header>
        <main>
            <form
                action="javascript:void(0)"
                class="pure-form pure-form-stacked"
            >
                <label for="url">Youtube URL</label>
                <input id="url" class="pure-input-1" readonly value={url}>
                <input
                    type="submit"
                    class="pure-button pure-button-primary"
                    style="pointer-events:none"
                >
            </form>
        </main>
    </article>
    <article>
        <header>3. Press "Submit" and wait</header>
        <main>
            <form
                action="javascript:void(0)"
                class="pure-form pure-form-stacked"
            >
                <label for="url">Youtube URL</label>
                <input id="url" class="pure-input-1" readonly value={url}>
                <input
                    type="submit"
                    class="pure-button pure-button-primary pure-button-active"
                    style="pointer-events:none"
                >
                <img src="/static/bars.png">
            </form>
        </main>
    </article>
    <article>
        <header>4. Download the MP3 file</header>
        <main>
            <a
                style="pointer-events:none"
                class="pure-button pure-button-primary"
            >Download MP3 file</a>
        </main>
    </article>
    '''
    form = f'''
    <h1>Download MP3</h1>
    <form
        hx-post="/download"
        hx-boost="true"
        hx-push-url="true"
        hx-target="this"
        hx-swap="outerHTML"
        class="pure-form pure-form-stacked"
    >
        <label for="url">Youtube URL</label>
        <input
            type="url"
            name="url"
            id="url"
            required
            placeholder="copy-paste the exact link"
            class="pure-input-1"
        >
        <input type="submit" class="pure-button pure-button-primary">
        <img
            class="htmx-indicator"
            src="/static/bars.svg"
            style="display:none"
            hx-on="load:this.style.removeProperty('display')"
        >
    </form>
    '''
    return responses.HTMLResponse(page(request, f'''
    <main class="pure-g">
        <div class="pure-u-1 pure-u-md-1-2">{guide}</div>
        <div class="pure-u-1 pure-u-md-1-2" id="content">{form}</div>
    </main>
    '''))


async def new_download(request: Request):
    form = await request.form()
    if request.method == "GET" or "url" not in form:
        return responses.RedirectResponse("/", status_code=303)
    download.download_url(form["url"])
    keys, count = [], 0
    while not (youtube_id := [key for key in keys if key in form["url"]]):
        if count > 30:
            return responses.HTMLResponse(page(request, f'''
            <p>URL "{form["url"]}" took too long to download, try again</p>
            <br>
            <a
                href="/"
                class="pure-button pure-button-primary"
                hx-boost="true"
            >Go back</a>
            '''))
        time.sleep(1)
        count += 1
        with open(os.path.join(OUTPUT, "downloads.csv"), "r") as csv_file:
            keys = [row["youtube_id"] for row in csv.DictReader(csv_file)]
    return responses.HTMLResponse(page(request, f'''
    <a
        href="/downloaded/{youtube_id[-1]}"
        class="pure-button pure-button-primary"
    >Download MP3 file</a>
    '''))


async def downloaded(request: Request):
    youtube_id = request.path_params["youtube_id"]
    directory = os.path.join(OUTPUT, youtube_id)
    if (not os.path.exists(directory) or len(os.listdir(directory)) != 1):
        return responses.HTMLResponse(page(request, f'''
        <div>File not found, download may still be in progress.</div>
        <a
            hx-on="click:
                document.getElementById('retry').removeAttribute('hidden')"
            class="pure-button"
        >Try again</a>
        <a
            id="retry"
            href
            hidden
            class="pure-button pure-button-primary"
        >Refresh</a>
        '''))
    file_name = os.listdir(directory)[-1]
    return responses.FileResponse(
        f'{directory}/{file_name}', media_type="mp3", filename=file_name
    )


app = applications.Starlette(
    debug=True,
    routes=[
        routing.Route("/", index),
        routing.Route("/download", new_download, methods=["GET", "POST"]),
        routing.Route("/downloaded/{youtube_id}", downloaded),
        routing.Mount("/static", staticfiles.StaticFiles(directory="static"))
    ]
)


if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8080, reload=True)
