
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

<p>Quick rundown of how this project is put together and what each file is for.
There are two parts, straight from the assignment:</p>
<ul>
  <li><b>Section 1 &mdash; denoising.</b> The airport image has three different
      kinds of noise, one on each colour channel. We clean all three and stitch
      them back into one image.</li>
  <li><b>Section 2 &mdash; finding the planes.</b> Cut out one plane, use it as a
      template, slide it over the image (at a bunch of rotations), and mark wherever
      it matches well.</li>
</ul>
<p>The one rule to remember: no built-in filtering functions allowed, except the
FFT. So the filters and the correlation are all hand-written; the only library
call we lean on is <code>numpy.fft</code>.</p>

<h2>1. How a run flows</h2>
<p><code>main.py</code> just runs the stages top to bottom and dumps a numbered
PNG for each one into <code>output/</code>:</p>
<pre>  load clean image  ->  add noise  ->  DENOISE  ->  crop template
        |                  |             |              |
     01_clean         02_noisy      03_denoised    04_template
                                                        |
                              rotate + match (NCC) + drop duplicates
                                                        |
                                         05_response  +  06_detections</pre>
<p>Why do we add the noise ourselves? The PDF only ships a <i>picture</i> of a
noisy image, not the actual data. So we recreate the three noise types it
describes on the clean image and then remove them &mdash; that way the denoising
is real and we can actually measure how much it helped (in dB).</p>

{summary_html}

<h2>2. Files</h2>
<table>
  <tr><th>File / folder</th><th>What it's for</th></tr>
  <tr><td><code>main.py</code></td><td>Runs everything in order and saves results.</td></tr>
  <tr><td><code>config.py</code></td><td>All the knobs/numbers in one place.</td></tr>
  <tr><td><code>imageutils.py</code></td><td>Load/save images, RGB &lt;-&gt; YCbCr.</td></tr>
  <tr><td><code>Noise.py</code></td><td>Builds the noisy test image (Section 1 input).</td></tr>
  <tr><td><code>filters.py</code></td><td>The hand-written filters: convolution,
      Gaussian, median, FFT notch.</td></tr>
  <tr><td><code>denoise.py</code></td><td>Section 1 &mdash; one filter per channel, recombine.</td></tr>
  <tr><td><code>ncc.py</code></td><td>The normalized cross-correlation (the matching maths).</td></tr>
  <tr><td><code>detect.py</code></td><td>Section 2 &mdash; rotate template, match, drop dupes, draw.</td></tr>
  <tr><td><code>make_docs.py</code></td><td>Generates this PDF.</td></tr>
  <tr><td><code>images/</code></td><td>The clean airport image (pulled from the PDF).</td></tr>
  <tr><td><code>output/</code></td><td>Generated results (made on first run).</td></tr>
  <tr><td><code>venv/</code></td><td>The Python environment with the libraries.</td></tr>
  <tr><td><code>.vscode/</code></td><td>So the Run button works without setup.</td></tr>
  <tr><td><code>RUN_ME.bat</code></td><td>Double-click to run the whole thing.</td></tr>
</table>

<h2>3. Why YCbCr?</h2>
<p>Instead of RGB we work in YCbCr, which splits the image into brightness
(<b>Y</b>) and two colour channels (<b>Cb</b>, <b>Cr</b>). The assignment puts a
different noise on each one, so keeping them separate lets us deal with each
problem on its own. <code>imageutils.py</code> does the RGB-to-YCbCr conversion at
the start and back again at the end.</p>

<h2>4. Section 1 &mdash; denoising, file by file</h2>

<h3>imageutils.py</h3>
<ul>
  <li><code>load_rgb</code> / <code>save_rgb</code> &mdash; read and write images (Pillow).</li>
  <li><code>rgb_to_ycbcr</code> / <code>ycbcr_to_rgb</code> &mdash; the colour conversion,
      written out with the BT.601 formulas so we control each channel directly.</li>
</ul>

<h3>Noise.py</h3>
<p>Adds the three noise types, one per channel:</p>
<ul>
  <li><code>add_gaussian</code> (Y) &mdash; random fuzz, like grain in a dark photo.</li>
  <li><code>add_salt_pepper</code> (Cb) &mdash; random pixels stuck at pure black or white.</li>
  <li><code>add_periodic</code> (Cr) &mdash; a repeating wavy stripe pattern.</li>
  <li><code>make_noisy</code> &mdash; applies all three. Uses a fixed random seed so
      every run comes out the same.</li>
</ul>

<h3>filters.py</h3>
<p>The actual filtering, all from scratch:</p>
<ul>
  <li><code>convolve2d</code> &mdash; generic 2-D convolution (slide a small grid of
      weights over the image). Everything spatial is built on this.</li>
  <li><code>gaussian_smooth</code> (Y) &mdash; a soft blur; averaging neighbours cancels
      out the random Gaussian fuzz.</li>
  <li><code>median_filter</code> (Cb) &mdash; take the median of each neighbourhood.
      Medians ignore extreme values, so the black/white dots just vanish.</li>
  <li><code>notch_reject_filter</code> (Cr) &mdash; the frequency-domain one. The stripe
      noise shows up as a couple of bright spikes in the FFT; we find those spikes,
      zero them out, and transform back.</li>
</ul>

<h3>denoise.py</h3>
<p><code>denoise_ycbcr</code> just wires it up: Y through the blur, Cb through the
median, Cr through the notch, then stack the three cleaned channels back together.
That single image is the Section 1 result.</p>

<h2>5. Section 2 &mdash; finding the planes, file by file</h2>

<h3>The idea</h3>
<p>Cut out one plane and use it as a stamp. Slide it over the whole image and at
every spot ask "how much does this look like the stamp?". The high-scoring spots
are planes.</p>

<h3>ncc.py</h3>
<p>The score is the normalized cross-correlation coefficient (Gonzalez &amp; Woods
eq. 12.2-8, the formula on the last page of the assignment). "Normalized" means it
sits in [-1, 1] and ignores overall brightness &mdash; it cares about shape, so a
plane in shadow still matches one in sunlight.</p>
<ul>
  <li><code>normalized_cross_correlation</code> &mdash; the fast version the pipeline
      uses (numerator via the FFT, local averages via integral images).</li>
  <li><code>normalized_cross_correlation_direct</code> &mdash; the plain double-loop
      version from the textbook. Slow, kept around as a sanity check that the fast
      one gives the same answer.</li>
  <li>the <code>mask</code> &mdash; when you rotate the template its corners become
      blank; the mask marks the real pixels so those corners don't skew the score.</li>
</ul>

<h3>detect.py</h3>
<ul>
  <li><code>build_rotated_templates</code> &mdash; planes point in different directions,
      so we rotate the template from -45&deg; to +45&deg; in 9&deg; steps (11 of them).</li>
  <li><code>response_map</code> &mdash; matches every rotated template across Y, Cb, Cr,
      blends the scores, keeps the best per pixel. This is <code>05_response.png</code>.</li>
  <li><code>non_max_suppression</code> &mdash; one plane lights up a whole blob of pixels;
      this keeps only the single strongest hit per blob so each plane counts once.</li>
  <li><code>find_airplanes</code> &mdash; runs the above and returns the final list.</li>
  <li><code>draw_detections</code> &mdash; draws the red circles for <code>06_detections.png</code>.</li>
</ul>

<h2>6. config.py (the knobs)</h2>
<p>Anything you'd want to tweak lives here, so you never have to touch the
algorithms. The handy ones:</p>
<table>
  <tr><th>Setting</th><th>What it does</th></tr>
  <tr><td><code>TEMPLATE_BOX</code></td><td>Which rectangle gets cut out as the template.</td></tr>
  <tr><td><code>ROTATION_MIN/MAX/STEP_DEG</code></td><td>The rotation range (-45 to +45, step 9).</td></tr>
  <tr><td><code>NCC_THRESHOLD</code></td><td>How good a match has to be. Higher = fewer
      but surer hits; lower = more hits but more false alarms.</td></tr>
  <tr><td><code>NMS_MIN_DISTANCE</code></td><td>How far apart two hits must be to count
      as two planes.</td></tr>
  <tr><td><code>GAUSSIAN_*, MEDIAN_*, NOTCH_*</code></td><td>The size/strength of each filter.</td></tr>
</table>

<h2>7. Running it</h2>
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

<h2>8. What lands in output/</h2>
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
