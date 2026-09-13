"""Compose private Build 2 form-review and reference-comparison boards."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "temp" / "roman-human-base-build2"
RENDERS = BUILD / "renders"
CONCEPT = ROOT / "assets" / "Concept" / "Characters" / "Roman-Grunt" / "roman-grunt-reforged-concept-v1-approved.png"
ORIGINALS = ROOT / "temp" / "roman-research" / "turnaround"

BG=(16,19,23); PANEL=(28,32,38); TEXT=(232,227,216); MUTED=(155,164,176); GOLD=(205,158,76)


def font(size, bold=False):
    path=Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path),size) if path.is_file() else ImageFont.load_default()


def label(draw,xy,text,size=28,color=TEXT,bold=False):
    draw.text(xy,text,font=font(size,bold),fill=color)


def fit(path,size,centering=(.5,.5)):
    return ImageOps.pad(Image.open(path).convert("RGB"),size,method=Image.Resampling.LANCZOS,color=PANEL,centering=centering)


def review_board():
    board=Image.new("RGB",(4800,2850),BG); draw=ImageDraw.Draw(board)
    label(draw,(90,55),"ROMAN GRUNT — BUILD 2 MAJOR-FORM GATE",52,GOLD,True)
    label(draw,(90,125),"AWAITING HUMAN VISUAL APPROVAL — BUILD 2",29,MUTED)
    views=[("roman-build2-front.png","FRONT"),("roman-build2-front-three-quarter.png","FRONT 3/4"),
           ("roman-build2-left-side.png","LEFT SIDE"),("roman-build2-rear-three-quarter.png","REAR 3/4"),
           ("roman-build2-rear.png","REAR")]
    x,y,w,h,gap=80,205,880,1510,70
    for name,title in views:
        board.paste(fit(RENDERS/name,(w,h)),(x,y)); label(draw,(x,y+h+15),title,27,TEXT,True); x+=w+gap
    details=[("roman-build2-helmet.png","HELMET / HEAD"),("roman-build2-torso-shoulders.png","TORSO + SHOULDERS"),
             ("roman-build2-waist-pteruges.png","WAIST / PTERUGES"),("roman-build2-shield.png","SHIELD"),
             ("roman-build2-footwear.png","FOOTWEAR")]
    x,y,w,h,gap=80,1815,880,820,70
    for name,title in details:
        board.paste(fit(RENDERS/name,(w,h)),(x,y)); label(draw,(x,y+h+12),title,25,TEXT,True); x+=w+gap
    path=RENDERS/"roman-build2-review.png"; board.save(path,optimize=True); return path


def comparison_board():
    board=Image.new("RGB",(4800,2300),BG); draw=ImageDraw.Draw(board)
    label(draw,(85,48),"ROMAN GRUNT — IDENTITY / CONCEPT / BUILD 2",50,GOLD,True)
    panels=[(ORIGINALS/"roman-standard-front-three-quarter.png","RECOVERED ORIGINAL PS2","Canonical identity / structure"),
            (CONCEPT,"APPROVED REFORGED CONCEPT","Primary modern visual target"),
            (RENDERS/"roman-build2-front-three-quarter.png","BUILD 2","Current moderate-complexity form gate")]
    x,y,w,h,gap=80,150,1500,1940,70
    for path,title,subtitle in panels:
        board.paste(fit(path,(w,h)),(x,y)); label(draw,(x,y+h+12),title,28,TEXT,True); label(draw,(x,y+h+52),subtitle,23,MUTED); x+=w+gap
    path=RENDERS/"roman-build2-reference-comparison.png"; board.save(path,optimize=True); return path


def crop_comparisons():
    rows=[
        ("HELMET / HEAD","roman-standard-closeup-head-helmet.png","roman-build2-helmet.png",(.50,.18)),
        ("TORSO + SHOULDERS","roman-standard-closeup-torso-armour.png","roman-build2-torso-shoulders.png",(.50,.40)),
        ("WAIST / PTERUGES","roman-standard-front.png","roman-build2-waist-pteruges.png",(.50,.64)),
        ("SHIELD","roman-standard-closeup-shield-front.png","roman-build2-shield.png",(.38,.52)),
        ("FOOTWEAR","roman-standard-front.png","roman-build2-footwear.png",(.50,.86)),
    ]
    board=Image.new("RGB",(4200,3600),BG); draw=ImageDraw.Draw(board)
    label(draw,(70,38),"BUILD 2 — MAJOR-FORM CROPPED COMPARISONS",48,GOLD,True)
    for row,(title,orig_name,build_name,concept_center) in enumerate(rows):
        y=125+row*690; label(draw,(70,y),title,27,TEXT,True)
        paths=[ORIGINALS/orig_name,CONCEPT,RENDERS/build_name]
        titles=["ORIGINAL","CONCEPT","BUILD 2"]
        for col,(path,sub) in enumerate(zip(paths,titles)):
            center=concept_center if col==1 else (.5,.5)
            img=fit(path,(1290,600),center); x=70+col*1370
            board.paste(img,(x,y+45)); label(draw,(x,y+650),sub,22,MUTED,True)
    path=RENDERS/"roman-build2-major-form-comparisons.png"; board.save(path,optimize=True); return path


def main():
    RENDERS.mkdir(parents=True,exist_ok=True)
    for path in (review_board(),comparison_board(),crop_comparisons()): print(path)


if __name__=="__main__": main()
