from __future__ import annotations

import logging
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Optional, Union, Iterator
from contextlib import contextmanager
from uuid import uuid4
from shutil import copyfile
import os

from PyPDF2 import PdfFileReader, PdfFileMerger, PdfFileWriter

from .util import crop_page_by, crop_page_to, scale_page_to

logger = logging.getLogger(__name__)


class WorkingCruncher:
    """PDF processing class wrapping a temporary PDF file.

    This should not be instantiated directly.
    It is produced by methods on the ``Cruncher`` class.
    The functionality of the classes are the same, except for `__exit__`.

    Where space in the temporary directory (e.g. RAM in tmpfs) is limiting,
    ``WorkingCruncher`` can be used as a context manager
    which deletes the temporary file on exit.
    """
    def __init__(
        self, path: Path, tmpdir: TemporaryDirectory
    ):
        self._path = Path(path)
        self._tmpdir = tmpdir

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_info, traceback):
        self.cleanup()

    def cleanup(self):
        """Clean up required temporary files"""
        self._path.unlink()

    def _new_child(self) -> Path:
        """Generate a random name for a new file in the tmpdir"""
        return Path(self._tmpdir.name) / f"{uuid4()}.pdf"

    @contextmanager
    def _reader(self):
        """Context manager for PdfFileReader wrapping this file"""
        with open(self._path, "rb") as r:
            reader = PdfFileReader(r)
            yield reader

    def _finalize(
        self, writer: Union[PdfFileWriter, PdfFileMerger]
    ) -> WorkingCruncher:
        """Write to a new temporary file and return a Cruncher over it"""
        fpath = self._new_child()
        with open(fpath, "wb") as f:
            writer.write(f)
        return WorkingCruncher(fpath, self._tmpdir)

    def write(self, fpath: Path) -> WorkingCruncher:
        """Save this Cruncher to a file"""
        fpath = Path(fpath)
        fpath.parent.mkdir(exist_ok=True, parents=True)
        copyfile(self._path, fpath)
        return self

    def __getitem__(self, idx: Union[int, slice]) -> WorkingCruncher:
        """Get specified pages from PDF"""
        writer = PdfFileWriter()
        with self._reader() as r:
            selection = r.pages[idx]
            if isinstance(idx, slice):
                for page in selection:
                    writer.addPage(page)
            else:
                writer.addPage(selection)
            return self._finalize(writer)

    def split(self) -> Iterator[WorkingCruncher]:
        """Iterate through Crunchers representing individual pages"""
        with self._reader() as r:
            for page in r.pages:
                writer = PdfFileWriter()
                writer.addPage(page)
                yield self._finalize(writer)

    def join(self, *args: Cruncher) -> WorkingCruncher:
        """Join this Cruncher with all given Crunchers."""
        merger = PdfFileMerger()
        for c in [self, *args]:
            merger.append(os.fspath(c._path))
        return self._finalize(merger)

    def rotate90cw(self, n: int = 1) -> WorkingCruncher:
        """Rotate every page by 90 degrees clockwise ``n`` times.

        ``n`` must be an integer.
        """
        writer = PdfFileWriter()
        with self._reader() as r:
            for page in r.pages:
                if n < 0:
                    writer.addPage(
                        page.rotateCounterClockwise(90 * int(abs(n)))
                    )
                else:
                    writer.addPage(page.rotateClockwise(90 * int(n)))
            return self._finalize(writer)

    def scale_by(self, x: float, y: Optional[float] = None) -> WorkingCruncher:
        """Scale every page by some ``x`` and ``y`` proportions.

        If ``y`` is ``None``, maintain aspect ratio.
        """
        writer = PdfFileWriter()
        with self._reader() as r:
            for page in r.pages:
                y = x if y is None else y
                page.scale(max(x, 0.0), max(y, 0.0))
                writer.addPage(page)
            return self._finalize(writer)

    def scale_to(self, width=None, height=None) -> WorkingCruncher:
        """Scale every page to the given user units.

        If either is None, maintain aspect ratio.
        If both are None, do not change anything.
        """
        writer = PdfFileWriter()
        with self._reader() as r:
            for p in r.pages:
                writer.addPage(scale_page_to(p, width, height))
            return self._finalize(writer)

    def crop_by(self, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0):
        """EXPERIMENTAL: crop every page by some proportion between 0 and 1.

        e.g. to take the lower left half of a page, use
        ``cruncher.crop_by(xmax=0.5, ymin=0.5)``.
        """
        writer = PdfFileWriter()
        with self._reader() as r:
            for p in r.pages:
                writer.addPage(crop_page_by(p, xmin, xmax, ymin, ymax))
            return self._finalize(writer)

    def crop_to(self, xmin=None, xmax=None, ymin=None, ymax=None):
        """EXPERIMENTAL: crop every page to given user units."""
        writer = PdfFileWriter()
        with self._reader() as r:
            for p in r.pages:
                writer.addPage(crop_page_to(p, xmin, xmax, ymin, ymax))
            return self._finalize(writer)


class Cruncher(WorkingCruncher):
    """PDF processing class wrapping a PDF file.

    Every method creates a temporary PDF file wrapped in a ``WorkingCruncher``,
    due to undefined behaviour in PyPDF2.
    When used as a context manager,
    Cruncher deletes all of the temporary files on __exit__.
    Otherwise, it is deleted with the ``cleanup`` method, or on destruction.
    """
    def __init__(self, path: Path):
        super().__init__(path, TemporaryDirectory(prefix="pdfcruncher"))

    def cleanup(self):
        self._tmpdir.cleanup()
