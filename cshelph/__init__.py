#!/usr/bin/env python
# coding: utf-8

'''
THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXpRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

from distutils.version import LooseVersion

CSHELPH_VERSION_MAJOR = 3
CSHELPH_VERSION_MINOR = 0
CSHELPH_VERSION_PATCH = 0

CSHELPH_VERSION = f"{CSHELPH_VERSION_MAJOR}.{CSHELPH_VERSION_MINOR}.{CSHELPH_VERSION_PATCH}"
CSHELPH_VERSION_OBJ = LooseVersion(CSHELPH_VERSION)
__version__ = CSHELPH_VERSION
