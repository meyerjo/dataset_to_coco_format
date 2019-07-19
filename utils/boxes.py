


class Boxes(object):
    def __init__(self, xmin, xmax, ymin, ymax, label):
        self.xmin = float(xmin)
        self.xmax = float(xmax)

        self.ymin = float(ymin)
        self.ymax = float(ymax)
        self.label = label

    def to_xyxy(self, normalization=None):
        assert(normalization is None or (
            isinstance(normalization, tuple),
            len(normalization) == 2
        ))
        if normalization is None:
            return [self.xmin, self.ymin, self.xmax, self.ymax]
        return [
            self.xmin / normalization[0], self.ymin / normalization[1],
            self.xmax / normalization[0], self.ymax / normalization[1]
        ]

    def to_xywh(self, normalization=None):
        assert(normalization is None or (
            isinstance(normalization, tuple),
            len(normalization) == 2
        ))
        w, h = self.dimension
        res = [self.xmin+w/2, self.ymin+h/2, w, h]
        if normalization is None:
            return res
        return [
            res[0] / normalization[0],
            res[1] / normalization[1],
            res[2] / normalization[0],
            res[3] / normalization[1]
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

