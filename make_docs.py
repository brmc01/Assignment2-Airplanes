# Builds Documentation.pdf from the HTML below (PyMuPDF). Run: python make_docs.py

import os
import fitz  # PyMuPDF

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(ROOT, "Documentation.pdf")
SUMMARY = os.path.join(ROOT, "output", "summary.png")

summary_html = (
    f'<p class="cap">summary.png: noisy -&gt; denoised -&gt; the template used -&gt; '
    f'the planes found.</p>'
    f'<img src="summary.png" width="620">'
    if os.path.exists(SUMMARY) else
    '<p><i>Run main.py first to generate output/summary.png.</i></p>'
)

HTML = f"""
<html>
<head><style>
  body  {{ font-family: serif; font-size: 11pt; color: #000; line-height: 1.4; }}
  h1    {{ font-size: 19pt; margin-bottom: 1px; }}
  h2    {{ font-size: 13.5pt; margin-top: 20px; margin-bottom: 4px; }}
  .sub  {{ font-size: 10.5pt; color: #444; margin-top: 0; }}
  code  {{ font-family: monospace; }}
  pre   {{ font-family: monospace; background: #f3f3f3; padding: 7px;
           font-size: 9pt; white-space: pre; }}
  table {{ border-collapse: collapse; font-size: 10pt; }}
  th, td {{ border: 1px solid #aaa; padding: 4px 7px; text-align: left;
           vertical-align: top; }}
  th    {{ font-weight: bold; }}
  .cap  {{ font-size: 9pt; color: #555; font-style: italic; margin-bottom: 3px; }}
</style></head>
<body>

<h1>Where are the Airplanes? &mdash; notes on the code</h1>
<p class="sub">Assignment 2, Image Processing (Prof. Zaghetto, UnB).</p>

<p>Short rundown of how this works. The whole project is three Python files plus a
script that makes this PDF. Two parts:</p>
<ul>
  <li><b>Section 1 &mdash; denoising.</b> Add gaussian noise to the image's
      brightness, then blur it back off.</li>
  <li><b>Section 2 &mdash; finding the planes.</b> Cut one plane out as a template,
      slide it over the image at a bunch of rotations, and circle wherever it
      matches well.</li>
</ul>
<p>The rule from the assignment: no built-in filtering functions, except the FFT.
So the blur and the matching are written by hand; the only library shortcut is
<code>numpy.fft</code>, used inside the matcher.</p>

<h2>How a run flows</h2>
<p><code>main.py</code> runs the stages top to bottom and saves a picture for each
one into <code>output/</code>:</p>
<pre>  load image  ->  add gaussian noise  ->  blur  ->  cut out template  ->  match
                       |                   |             |                  |
                   01_noisy          02_denoised    03_template      04_detections</pre>
<p>Why add the noise ourselves? The PDF only ships a <i>picture</i> of a noisy
image, not the real data. So we add gaussian noise to the clean image and then
remove it &mdash; that way the denoising is real and we can measure it (PSNR, dB).</p>

{summary_html}

<h2>The files</h2>
<table>
  <tr><th>File / folder</th><th>What it's for</th></tr>
  <tr><td><code>main.py</code></td><td>Runs everything. Also holds the small helpers
      (load/save images, RGB &lt;-&gt; YCbCr, PSNR) and the template location.</td></tr>
  <tr><td><code>denoising.py</code></td><td>Section 1: adds the gaussian noise and the
      hand-written blur that removes it.</td></tr>
  <tr><td><code>detection.py</code></td><td>Section 2: the normalized cross-correlation
      plus the rotate / match / dedupe / draw steps.</td></tr>
  <tr><td><code>make_docs.py</code></td><td>Builds this PDF.</td></tr>
  <tr><td><code>images/</code></td><td>The clean airport image (pulled from the PDF).</td></tr>
  <tr><td><code>output/</code></td><td>Generated results (made on first run).</td></tr>
  <tr><td><code>venv/</code></td><td>The Python environment with the libraries.</td></tr>
  <tr><td><code>RUN_ME.bat</code></td><td>Double-click to run the whole thing.</td></tr>
</table>

<h2>Why YCbCr?</h2>
<p>We convert the image to YCbCr, which splits it into brightness (<b>Y</b>) and two
colour channels (<b>Cb</b>, <b>Cr</b>). The gaussian noise goes on Y and the blur
cleans Y, so working in YCbCr lets us touch the brightness without messing with the
colours. <code>main.py</code> converts RGB to YCbCr at the start and back at the end.</p>

<h2>Section 1 &mdash; denoising.py</h2>
<p>The settings (noise amount and blur size) sit at the top of the file.</p>
<ul>
  <li><code>add_noise</code> &mdash; adds gaussian fuzz to the Y channel. A fixed
      random seed keeps every run the same.</li>
  <li><code>convolve</code> &mdash; plain 2D convolution (slide a small grid of
      weights over the image). The blur is built on this.</li>
  <li><code>gaussian_kernel</code> &mdash; makes the little bell-shaped grid of weights.</li>
  <li><code>blur</code> &mdash; convolves Y with that kernel; averaging neighbours
      cancels the random noise.</li>
  <li><code>denoise</code> &mdash; blurs the Y channel and returns the cleaned image.</li>
</ul>

<h2>Section 2 &mdash; detection.py</h2>
<p>Idea: cut out one plane and use it as a stamp. Slide it over the image and at
every spot ask "how much does this look like the stamp?". The high-scoring spots
are planes. Settings are at the top of the file.</p>
<ul>
  <li><code>ncc</code> &mdash; the normalized cross-correlation score (Gonzalez &amp;
      Woods eq. 12.2-8, the formula on the last page of the assignment). It's in
      [-1, 1] and ignores brightness, so it matches shape &mdash; a plane in shadow
      still matches one in sunlight. The top of the fraction uses the FFT; the
      bottom uses running sums so it's quick.</li>
  <li><code>find_planes</code> &mdash; rotates the template from -45&deg; to +45&deg;
      in 9&deg; steps (11 angles), matches every rotation, and keeps the best score
      per pixel. The mask it builds marks the real template pixels so the blank
      corners from rotating don't skew the score.</li>
  <li><code>_dedupe</code> &mdash; one plane lights up a whole blob of pixels, so this
      keeps only the single strongest hit per area.</li>
  <li><code>draw</code> &mdash; draws the red circles for <code>04_detections.png</code>.</li>
</ul>

<h2>Tweaking it</h2>
<table>
  <tr><th>Setting</th><th>What it does</th></tr>
  <tr><td><code>GAUSS_SIGMA</code> (denoising.py)</td><td>How much noise to add.</td></tr>
  <tr><td><code>GAUSS_SIZE</code> (denoising.py)</td><td>How strong the blur is.</td></tr>
  <tr><td><code>TEMPLATE_BOX</code> (main.py)</td><td>Which rectangle gets cut out as the template.</td></tr>
  <tr><td><code>THRESHOLD</code> (detection.py)</td><td>How good a match has to be. Higher =
      fewer but surer hits; lower = more hits but more false alarms.</td></tr>
  <tr><td><code>MIN_GAP</code> (detection.py)</td><td>How far apart two hits must be to count as two planes.</td></tr>
  <tr><td><code>ROT_MIN/MAX/STEP</code> (detection.py)</td><td>The rotation range (-45 to +45, step 9).</td></tr>
</table>

<h2>Running it</h2>
<p>Easiest: double-click <code>RUN_ME.bat</code> (first run sets up the environment).
In VSCode: open this folder and press <b>F5</b>, or just hit the Run button on
<code>main.py</code> &mdash; it re-launches itself with the right Python either way.
From a terminal:</p>
<pre>./venv/Scripts/python.exe main.py            # run, show window, open output
./venv/Scripts/python.exe main.py --no-show  # just write the files</pre>
<p>You get progress in the terminal, a window with the four pictures, and the
output folder opening. It also prints the PSNR and each plane's location/score/angle.</p>

<h2>What lands in output/</h2>
<table>
  <tr><th>File</th><th>What it is</th></tr>
  <tr><td><code>01_noisy.png</code></td><td>The image after gaussian noise.</td></tr>
  <tr><td><code>02_denoised.png</code></td><td>After the blur (Section 1 result).</td></tr>
  <tr><td><code>03_template.png</code></td><td>The plane template that got cut out.</td></tr>
  <tr><td><code>04_detections.png</code></td><td>Section 2 result &mdash; planes circled.</td></tr>
  <tr><td><code>summary.png</code></td><td>All four pictures in one image.</td></tr>
</table>

</body>
</html>
"""


def build():
    archive = fitz.Archive(os.path.join(ROOT, "output")) if os.path.exists(SUMMARY) else None
    story = fitz.Story(html=HTML, archive=archive)
    writer = fitz.DocumentWriter(OUT_PDF)

    mediabox = fitz.paper_rect("a4")
    where = mediabox + (48, 48, -48, -55)

    more = 1
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    build()
