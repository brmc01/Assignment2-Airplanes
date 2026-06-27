# Builds Documentation.pdf from the HTML below (PyMuPDF). Run: python make_docs.py

import os
import fitz  # PyMuPDF

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(ROOT, "Documentation.pdf")
SUMMARY = os.path.join(ROOT, "output", "summary.png")

summary_html = (
    f'<p class="cap">summary.png: clean -&gt; noisy -&gt; denoised, the template, '
    f'the Cr spectrum before/after the notch, the match heatmap, and the detections.</p>'
    f'<img src="summary.png" width="600">'
    if os.path.exists(SUMMARY) else
    '<p><i>Run main.py first to generate output/summary.png.</i></p>'
)

HTML = f"""
<html>
<head><style>
  body  {{ font-family: serif; font-size: 11pt; color: #000; line-height: 1.4; }}
  h1    {{ font-size: 19pt; margin-bottom: 1px; }}
  h2    {{ font-size: 13.5pt; margin-top: 20px; margin-bottom: 4px; }}
  h3    {{ font-size: 11.5pt; margin-top: 13px; margin-bottom: 2px; }}
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

<p>Short rundown of how this thing works. The whole project is just three Python
files plus a script that makes this PDF. There are two parts, straight from the
assignment:</p>
<ul>
  <li><b>Section 1 &mdash; denoising.</b> The airport image has three different
      kinds of noise, one on each colour channel. We clean all three off and put
      the image back together.</li>
  <li><b>Section 2 &mdash; finding the planes.</b> Cut one plane out as a template,
      slide it over the image at a bunch of rotations, and mark wherever it matches
      well.</li>
</ul>
<p>The rule to remember: no built-in filtering functions, except the FFT. So the
filters and the matching are all hand-written; the only library call we lean on is
<code>numpy.fft</code>.</p>

<h2>How a run flows</h2>
<p><code>main.py</code> runs the stages top to bottom and saves a numbered PNG for
each one into <code>output/</code>:</p>
<pre>  load image  ->  add noise  ->  DENOISE  ->  cut out template
       |              |            |               |
   01_clean      02_noisy     03_denoised     04_template
                                                  |
                          rotate + match + drop duplicates
                                                  |
                                   05_response  +  06_detections</pre>
<p>Why add the noise ourselves? The PDF only ships a <i>picture</i> of a noisy
image, not the real data. So we recreate the three noise types it describes on the
clean image and then remove them &mdash; that way the denoising is real and we can
measure how much it helped (in dB).</p>

{summary_html}

<h2>The files</h2>
<table>
  <tr><th>File / folder</th><th>What it's for</th></tr>
  <tr><td><code>main.py</code></td><td>Runs everything. Also holds the small helpers
      (load/save images, RGB &lt;-&gt; YCbCr, PSNR) and the template location.</td></tr>
  <tr><td><code>denoising.py</code></td><td>Section 1: adds the three noises and the
      three filters (gaussian, median, FFT notch).</td></tr>
  <tr><td><code>detection.py</code></td><td>Section 2: the normalized cross-correlation
      plus the rotate / match / dedupe / draw steps.</td></tr>
  <tr><td><code>make_docs.py</code></td><td>Builds this PDF.</td></tr>
  <tr><td><code>images/</code></td><td>The clean airport image (pulled from the PDF).</td></tr>
  <tr><td><code>output/</code></td><td>Generated results (made on first run).</td></tr>
  <tr><td><code>venv/</code></td><td>The Python environment with the libraries.</td></tr>
  <tr><td><code>.vscode/</code></td><td>So the Run button works without setup.</td></tr>
  <tr><td><code>RUN_ME.bat</code></td><td>Double-click to run the whole thing.</td></tr>
</table>

<h2>Why YCbCr?</h2>
<p>Instead of RGB we work in YCbCr, which splits the image into brightness
(<b>Y</b>) and two colour channels (<b>Cb</b>, <b>Cr</b>). The assignment puts a
different noise on each one, so keeping them separate lets us deal with each
problem on its own. <code>main.py</code> does the RGB-to-YCbCr conversion at the
start and converts back at the end.</p>

<h2>Section 1 &mdash; denoising.py</h2>
<p>The settings (noise levels and filter sizes) sit at the top of the file. The
functions:</p>
<ul>
  <li><code>add_noise</code> &mdash; puts the three noises on the three channels:
      gaussian fuzz on Y, salt &amp; pepper on Cb, a diagonal wave on Cr. A fixed
      random seed keeps every run the same.</li>
  <li><code>convolve</code> &mdash; plain 2D convolution (slide a small grid of
      weights over the image). The spatial filters are built on this.</li>
  <li><code>blur</code> (Y) &mdash; a soft gaussian blur; averaging neighbours cancels
      the random fuzz.</li>
  <li><code>median</code> (Cb) &mdash; takes the median of each little window, which
      ignores the black/white salt &amp; pepper spikes.</li>
  <li><code>notch</code> (Cr) &mdash; the frequency one. The wave shows up as a couple
      of bright spikes in the FFT; we find them, zero them out, and transform back.</li>
  <li><code>denoise</code> &mdash; runs one filter per channel and stacks them back
      into a single image (the Section 1 result).</li>
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
      in 9&deg; steps (11 angles), matches every rotation across Y/Cb/Cr, blends the
      scores, and keeps the best score per pixel. The mask it builds marks the real
      template pixels so the blank corners from rotating don't skew the score.</li>
  <li><code>_dedupe</code> &mdash; one plane lights up a whole blob of pixels, so this
      keeps only the single strongest hit per area.</li>
  <li><code>draw</code> &mdash; draws the red circles for <code>06_detections.png</code>.</li>
</ul>

<h2>Tweaking it</h2>
<p>The numbers you'd want to change are the constants at the top of
<code>denoising.py</code> and <code>detection.py</code>. The handy ones:</p>
<table>
  <tr><th>Setting</th><th>What it does</th></tr>
  <tr><td><code>TEMPLATE_BOX</code> (main.py)</td><td>Which rectangle gets cut out as the template.</td></tr>
  <tr><td><code>THRESHOLD</code> (detection.py)</td><td>How good a match has to be. Higher =
      fewer but surer hits; lower = more hits but more false alarms.</td></tr>
  <tr><td><code>MIN_GAP</code> (detection.py)</td><td>How far apart two hits must be to count as two planes.</td></tr>
  <tr><td><code>ROT_MIN/MAX/STEP</code> (detection.py)</td><td>The rotation range (-45 to +45, step 9).</td></tr>
  <tr><td><code>GAUSS_*, MEDIAN_*, NOTCH_*</code> (denoising.py)</td><td>The size/strength of each filter.</td></tr>
</table>

<h2>Running it</h2>
<p>Easiest: double-click <code>RUN_ME.bat</code> (first run sets up the environment,
takes about a minute).</p>
<p>In VSCode: open this folder, install the Python extension if it asks, hit
<b>F5</b> and pick "Run Assignment (show results)". The interpreter is already
pointed at the venv, so there's nothing to configure.</p>
<p>From a terminal:</p>
<pre>./venv/Scripts/python.exe main.py            # run, show window, open output
./venv/Scripts/python.exe main.py --no-show  # just write the files</pre>
<p>Either way you get progress in the terminal, a window with all the stages, and
the output folder opening. It also prints the PSNR (how much denoising helped, in
dB) and the coordinates/score/angle of each plane found.</p>

<h2>What lands in output/</h2>
<table>
  <tr><th>File</th><th>What it is</th></tr>
  <tr><td><code>01_clean.png</code></td><td>The base airport image.</td></tr>
  <tr><td><code>02_noisy.png</code></td><td>After the three noise types.</td></tr>
  <tr><td><code>03_denoised.png</code></td><td>Section 1 result &mdash; the cleaned image.</td></tr>
  <tr><td><code>04_template.png</code></td><td>The template that got cut out.</td></tr>
  <tr><td><code>05_response.png</code></td><td>The match heatmap (bright = looks like a plane).</td></tr>
  <tr><td><code>06_detections.png</code></td><td>Section 2 result &mdash; planes circled.</td></tr>
  <tr><td><code>summary.png</code></td><td>All the stages in one image.</td></tr>
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
