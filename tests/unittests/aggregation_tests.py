"""
FiftyOne aggregation-related unit tests.

| Copyright 2017-2021, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import unittest

import fiftyone as fo

from decorators import drop_datasets


class DatasetTests(unittest.TestCase):
    @drop_datasets
    def test_order(self):
        d = fo.Dataset()
        s = fo.Sample(filepath="image.jpeg")
        s["number"] = 0
        s["numbers"] = [0, 1]
        d.add_sample(s)
        results = d.aggregate([fo.Count("number"), fo.Count("numbers")])
        self.assertEqual(results[0], 1)
        self.assertEqual(results[1], 2)

    @drop_datasets
    def test_bounds(self):
        d = fo.Dataset()
        d.add_sample_field("numbers", fo.ListField, subfield=fo.IntField())
        s = fo.Sample(filepath="image.jpeg")
        s["number"] = 0
        s["numbers"] = [0, 1]
        d.add_sample(s)
        self.assertEqual(d.aggregate(fo.Bounds("number")), (0, 0))
        self.assertEqual(d.aggregate(fo.Bounds("numbers")), (0, 1))

        d = fo.Dataset()
        s = fo.Sample(filepath="video.mp4")
        d.add_sample(s)
        d.add_frame_field("numbers", fo.ListField, subfield=fo.IntField())
        s[1]["number"] = 0
        s[1]["numbers"] = [0, 1]
        s.save()
        self.assertEqual(d.aggregate(fo.Bounds("frames.number")), (0, 0))
        self.assertEqual(d.aggregate(fo.Bounds("frames.numbers")), (0, 1))

        d = fo.Dataset()
        s = fo.Sample(filepath="image.jpeg")
        s["detection"] = fo.Detection(label="label", confidence=1)
        d.add_sample(s)
        self.assertEqual(
            d.aggregate(fo.Bounds("detection.confidence")), (1, 1)
        )
        s["detections"] = fo.Detections(
            detections=[
                fo.Detection(label="label", confidence=1),
                fo.Detection(label="label", confidence=0),
            ]
        )
        s.save()
        self.assertEqual(
            d.aggregate(fo.Bounds("detections.detections.confidence")), (0, 1),
        )

        d = fo.Dataset()
        s = fo.Sample(filepath="video.mp4")
        s[1]["detection"] = fo.Detection(label="label", confidence=1)
        d.add_sample(s)
        self.assertEqual(
            d.aggregate(fo.Bounds("frames.detection.confidence")), (1, 1),
        )

    @drop_datasets
    def test_count(self):
        d = fo.Dataset()
        s = fo.Sample(filepath="image.jpeg")
        v = d.view()
        self.assertEqual(d.aggregate(fo.Count()), 0)
        self.assertEqual(d.aggregate(fo.Count()), 0)
        d.add_sample(s)
        self.assertEqual(d.aggregate(fo.Count()), 1)
        self.assertEqual(d.aggregate(fo.Count()), 1)
        s["single"] = fo.Classification()
        s["list"] = fo.Classifications(
            classifications=[fo.Classification()] * 2
        )
        s["empty"] = fo.Classifications()
        s.save()
        self.assertEqual(d.aggregate(fo.Count("single")), 1)
        self.assertEqual(d.aggregate(fo.Count("list.classifications")), 2)
        self.assertEqual(d.aggregate(fo.Count("empty.classifications")), 0)

        d = fo.Dataset()
        s = fo.Sample(filepath="video.mp4")
        s[1]["value"] = "value"
        s[2]["value"] = "value"
        d.add_sample(s)
        self.assertEqual(d.aggregate(fo.Count("frames")), 2)

    @drop_datasets
    def test_count_values(self):
        d = fo.Dataset()
        s = fo.Sample(filepath="image.jpeg")
        # pylint: disable=no-member
        s.tags += ["one", "two"]
        d.add_sample(s)
        self.assertEqual(
            d.aggregate(fo.CountValues("tags")), {"one": 1, "two": 1}
        )

        d = fo.Dataset()
        s = fo.Sample(filepath="video.mp4")
        s["classifications"] = fo.Classifications(
            classifications=[
                fo.Classification(label="one"),
                fo.Classification(label="two"),
                fo.Classification(label="two"),
            ]
        )
        s[1]["classifications"] = fo.Classifications(
            classifications=[
                fo.Classification(label="one"),
                fo.Classification(label="two"),
                fo.Classification(label="two"),
            ]
        )
        s["classification"] = fo.Classification(label="one")
        d.add_sample(s)
        self.assertEqual(
            d.aggregate(fo.CountValues("classification.label")), {"one": 1}
        )
        self.assertEqual(
            d.aggregate(
                fo.CountValues("classifications.classifications.label")
            ),
            {"one": 1, "two": 2},
        )
        self.assertEqual(
            d.aggregate(
                fo.CountValues("frames.classifications.classifications.label")
            ),
            {"one": 1, "two": 2},
        )

    @drop_datasets
    def test_distinct(self):
        d = fo.Dataset()
        d.add_sample_field("strings", fo.ListField, subfield=fo.StringField())
        s = fo.Sample(filepath="image.jpeg")
        s["string"] = "string"
        s["strings"] = ["one", "two"]
        d.add_sample(s)
        self.assertEqual(d.aggregate(fo.Distinct("string")), ["string"])
        self.assertEqual(d.aggregate(fo.Distinct("strings")), ["one", "two"])

        d = fo.Dataset()
        s = fo.Sample(filepath="video.mp4")

        s = fo.Sample(filepath="image.jpeg")
        d.add_sample(s)
        s["classification"] = fo.Classification(label="label", confidence=1)
        s.save()
        self.assertEqual(
            d.aggregate(fo.Distinct("classification.label")), ["label"]
        )
        s["classifications"] = fo.Classifications(
            classifications=[
                fo.Classification(label="one"),
                fo.Classification(label="two"),
            ]
        )
        s.save()
        self.assertEqual(
            d.aggregate(fo.Distinct("classifications.classifications.label")),
            ["one", "two"],
        )

        d = fo.Dataset()
        s = fo.Sample(filepath="video.mp4")
        s[1]["classification"] = fo.Classification(label="label", confidence=1)
        d.add_sample(s)
        self.assertEqual(
            d.aggregate(fo.Distinct("frames.classification.label")), ["label"],
        )

    @drop_datasets
    def test_sum(self):
        d = fo.Dataset()
        d.add_sample_field("numeric_field", fo.IntField)
        self.assertEqual(d.aggregate(fo.Sum("numeric_field")), 0)
        s = fo.Sample(filepath="image.jpeg", numeric_field=1)
        d.add_sample(s)
        self.assertEqual(d.aggregate(fo.Sum("numeric_field")), 1)
        s = fo.Sample(filepath="image2.jpeg", numeric_field=2)
        d.add_sample(s)
        self.assertEqual(d.aggregate(fo.Sum("numeric_field")), 3)


if __name__ == "__main__":
    fo.config.show_progress_bars = False
    unittest.main(verbosity=2)
