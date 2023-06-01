import os
import pathlib

from starlette import applications, requests, responses, routing, staticfiles
import pytube


OUTPUT = os.path.join(pathlib.Path(__file__).parent.resolve(), "output")


def page(request: requests.Request, content: str) -> str:
    if request.headers.get("hx-boosted"):
        return content
    return f'''
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title id="title">Youtube to MP3</title>
            <link rel="icon" href="/static/smile.ico">
            <link rel="stylesheet" href="/static/pure-min.css">
            <link rel="stylesheet" href="/static/grids-responsive-min.css">
        </head>
        <style>
            body{{padding:1rem}}body>main{{max-width:60em;margin:0 auto}}
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


async def index(request: requests.Request):
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
        <header>3. Submit and wait for download</header>
    </article>
    '''
    form = f'''
    <h1>Download MP3</h1>
    <form
        action="/download"
        method="POST"
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
    </form>
    '''
    return responses.HTMLResponse(page(request, f'''
    <main class="pure-g">
        <div class="pure-u-1 pure-u-md-1-2">{guide}</div>
        <div class="pure-u-1 pure-u-md-1-2" id="content">{form}</div>
    </main>
    '''))


async def download(request: requests.Request):
    form = await request.form()
    if request.method == "GET" or "url" not in form:
        return responses.RedirectResponse("/", status_code=303)
    audio = pytube.YouTube(form["url"]).streams.get_audio_only()
    try:
        return responses.StreamingResponse(
            pytube.request.stream(audio.url),
            headers={
                "Content-Disposition":
                    f'attachment; filename="{audio.title}.mp3"'
            }
        )
    except UnicodeEncodeError:
        return responses.StreamingResponse(
            pytube.request.stream(audio.url),
            headers={
                "Content-Disposition":
                    f'attachment; filename="download.mp3"'
            }
        )


app = applications.Starlette(
    routes=[
        routing.Route("/", index),
        routing.Route("/download", download, methods=["GET", "POST"]),
        routing.Mount("/static", staticfiles.StaticFiles(directory="static"))
    ]
)
