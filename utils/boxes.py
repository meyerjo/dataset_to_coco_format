


class Boxes(object):

    class Normalizer(object):
        def __init__(self, width, height):
            self.w = width
            self.h = height

        @property
        def width(self):
            return self.w

        @property
        def height(self):
            return self.h


    def __init__(self, xmin, xmax, ymin, ymax, label):
        assert(ymin <= ymax and xmin <= xmax)
        self.xmin = float(xmin)
        self.xmax = float(xmax)

        self.ymin = float(ymin)
        self.ymax = float(ymax)
        self.label = label

    def to_xyxy(self, normalization=None):
        assert(normalization is None or
               isinstance(normalization, Boxes.Normalizer))
        if normalization is None:
            return [self.xmin, self.ymin, self.xmax, self.ymax]
        return [
            self.xmin / normalization.width, self.ymin / normalization.height,
            self.xmax / normalization.width, self.ymax / normalization.height
        ]

    def to_xywh(self, normalization=None):
        assert(normalization is None or
               isinstance(normalization, Boxes.Normalizer))
        w, h = self.dimension
        res = [self.xmin, self.ymin, w, h]
        if normalization is None:
            return res
        return [
            res[0] / normalization.width,
            res[1] / normalization.height,
            res[2] / normalization.width,
            res[3] / normalization.height
        ]

    def to_xcycwh(self, normalization=None):
        assert(normalization is None or
               isinstance(normalization, Boxes.Normalizer))
        w, h = self.dimension
        res = [self.xmin+w/2, self.ymin+h/2, w, h]
        if normalization is None:
            return res
        return [
            res[0] / normalization.width,
            res[1] / normalization.height,
            res[2] / normalization.width,
            res[3] / normalization.height
        ]

    @property
    def dimension(self):
        """
        :return: (width, height)
        """
        return (self.xmax - self.xmin, self.ymax - self.ymin)

    @property
    def size(self):
        w, h = self.dimension
        return w * h

