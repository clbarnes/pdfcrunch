import logging

from PyPDF2.pdf import PageObject, RectangleObject

logger = logging.getLogger(__name__)


def crop_box_to(
    box: RectangleObject, xmin=None, xmax=None, ymin=None, ymax=None
) -> RectangleObject:
    b_ymin, b_xmin = box.upperLeft
    b_ymax, b_xmax = box.lowerRight

    if xmin is None:
        xmin = b_xmin
    if xmax is None:
        xmax = b_xmax
    if ymin is None:
        ymin = b_ymin
    if ymax is None:
        ymax = b_ymax

    box.upperLeft = (max(ymin, b_ymin), max(xmin, b_xmin))
    box.lowerRight = (min(ymax, b_ymax), min(xmax, b_xmax))
    return box


def crop_page_to(
    page: PageObject, xmin=None, xmax=None, ymin=None, ymax=None
) -> PageObject:
    # TODO: how do these boxes interact?
    for box in [page.mediaBox, page.trimBox, page.cropBox]:
        crop_box_to(box, xmin, xmax, ymin, ymax)
    return page


def crop_page_by(
    page: PageObject, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0
) -> PageObject:
    b = page.mediaBox
    p_ymin, p_xmin = b.upperLeft
    p_ymax, p_xmax = b.lowerRight
    return crop_page_to(
        page,
        p_xmin * max(xmin, 0.0),
        p_xmax * min(xmax, 1.0),
        p_ymin * max(ymin, 0.0),
        p_ymax * min(ymax, 1.0)
    )


def scale_page_to(page: PageObject, width=None, height=None) -> PageObject:
    n_none = width is None + height is None
    if n_none == 2:
        return page

    if n_none == 1:
        p_width = float(
            page.mediaBox.getUpperRight_x() - page.mediaBox.getLowerLeft_x()
        )
        p_height = float(
            page.mediaBox.getUpperRight_y() - page.mediaBox.getLowerLeft_y()
        )
        if width is None:
            scale = height / p_height
            width = p_width * scale
        if height is None:
            scale = width / p_width
            height = p_height * scale

    page.scaleTo(width, height)
    return page
