import requests
import os
import shutil
import uuid


def _get_url_params(url):
    query = requests.utils.urlparse(url).query
    params = dict(x.split('=') for x in query.split('&'))
    return params

def _get_presentation_id(url):
    params = _get_url_params(url)
    eurl = params.get("pi")
    source_url = "https://www.brainshark.com/brainshark/brainshark.services.player/api/v1.0/Vu?nodesktopflash=1&pantherPlayerEnabled=true&company=mstc&pi={}&fb=0"
    source_url = source_url.format(eurl)

    s = requests.Session()
    # get the presentation id
    if (eurl):
        res = s.get(source_url)
        if res.json():
            presentation_id = res.json().get("bsplayer").get("presentationId")
            return presentation_id
    return None

def _get_asset_urls(s, asset_id):
    source = "https://www.brainshark.com/brainshark/brainshark.services.content/api/v1.0/SlideAssets/{}/Cheetah?accessTimeInMinutes=3600"
    source = source.format(asset_id)
    response = s.get(source)
    result = []
    if (response.json()):
        image_assets = response.json().get("CheetahImageAssets")
        for asset in image_assets:
            name = asset.get("Asset").get("AssetName")
            url = asset.get("Asset").get("AssetUrl")
            result.append((name, url))
        return result
    else:
        print "Unable to parse image asset urls"
        exit()


def _set_bsstok(s, url):
    # get session info with bsstok
    source = "https://www.brainshark.com/brainshark/brainshark.services.player/api/v1.0/SessionState?json=1&pi=611217056&referringurl={}"
    source = source.format(url)
    res = s.get(source)
    if (res.json()):
        bsstok = res.json().get("session").get("bsstok")
        s.headers["Brainshark-STok"] = bsstok
        return s
    else:
        print "Brainshark-STok not found"
        exit()

def download(url):
    presentation_id = _get_presentation_id(url)
    pres_url = "https://www.brainshark.com/brainshark/brainshark.services.player/api/v1.0/Presentation?pi={}"
    s = requests.Session()
    s = _set_bsstok(s, url)

    if presentation_id:
        # download the presentation
        pres_url = pres_url.format(presentation_id)
        presentation = s.get(pres_url).json()

        # create a directory for this presentation and cd into it
        presentation_name = presentation.get("title")
        if (not presentation_name): presentation_name = "Presentation"
        parent_folder = presentation_name + "-" + str(presentation_id)
        # child_folder = parent_folder + "/" + presentation_name
        try:
            os.mkdir(parent_folder)
            os.chdir(parent_folder)
        except OSError as e:
            print parent_folder + " already exists"
            return

        # get the content
        slides = presentation.get("slides")
        slidenotes = presentation.get("slidenotes")
        if (slides): slides = slides.get("slide")
        if (slidenotes): slidenotes = slidenotes.get("slide")
        else: slidenotes = [None] * len(slides)
        content = zip(slides, slidenotes)
       
        for index, (slide, note) in enumerate(zip(slides, slidenotes)):
            # create a sub-directory for these slides
            title = slide.get("title")
            if not title: title = "Slide"
            title = "{} - {}".format(index + 1, title.encode("utf-8"))
            print title
            os.mkdir(title)
            os.chdir(title)

            # get the audio and save them as mp3
            audio = "https://www.brainshark.com/brainshark/brainshark.services.player/api/v1.0/SlideAudio?pi={}&ver=0&sln={}&typ=AUD&sky=x"
            audio = audio.format(presentation_id, index + 1)
            audio_response = s.get(audio)
            if audio_response.content:
                with open("audio.mp3", "wb") as f:
                    f.write(audio_response.content)

            # save the notes
            if note:
                with open("notes.txt", "w") as f:
                    f.write(note.get("notes"))

            # get the images
            assets = _get_asset_urls(s, slide.get("id"))
            for asset in assets:
                byte_data = s.get(asset[1]).content
                with open(asset[0], "wb") as f:
                    f.write(byte_data)

            # cd back to the parent directory
            os.chdir("..")
            break

        # go back to project root
        os.chdir("..")

        # compress the file
        archive = "Archive"
        try:
            os.mkdir(archive)
        except OSError as e:
            print archive + " directory already exists"
        os.chdir(archive)
        zip_name = parent_folder.replace("-", "_").replace(" ", "_")
        shutil.make_archive(zip_name, 'zip', "../" + parent_folder)
        os.chdir("..")

download("https://www.brainshark.com/1/player/en/mstc?pi=zD9zi8nUjz0z0&fb=0")
