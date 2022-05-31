#!/usr/bin/env python3

import numpy as np


def img_avg(img):
    avg_colour_per_row = np.average(img, axis=0)
    avg_colour = np.average(avg_colour_per_row, axis=0)
    return avg_colour


IMAGE_SIZE = 32


class QuadImage:
    def __init__(self, high_res_image: np.ndarray, divisions: int):
        if divisions > 5:
            raise ValueError("Can't divide the image by more than 5 times")

        self.divisions = divisions

        self.image_representation = np.zeros(shape=(2 ** divisions, 2 ** divisions, 3))
        # pixels_per_cell
        ppc = int(IMAGE_SIZE / 2 ** divisions)

        for row in range(divisions):
            for col in range(divisions):
                colstart = col * ppc
                colend = (col + 1) * ppc
                rowstart = row * ppc
                rowend = (row + 1) * ppc
                self.image_representation[row][col] = img_avg(
                    high_res_image[colstart:colend, rowstart:rowend]
                )

    def __eq__(self, other):
        assert type(self) == type(other), "types must be the same"
        assert (
            self.divisions == other.divisions
        ), f"cannot compare divsions: {self.divisions} and divisions: {other.divisions} quadimages"
        return np.allclose(
            self.image_representation, other.image_representation, rtol=0, atol=1
        )


class RootImg(QuadImage):
    def __init__(self):
        self.divisions = -1

    def __eq__(self, other):
        raise Exception("Should not be comparing to root node")


class QuadImageQuery:
    def __init__(self, high_res_image: np.ndarray):
        self.divisions = 0
        self.initial_image = high_res_image
        self.quad_image = QuadImage(self.initial_image, self.divisions)

    def divided(self):
        divided_query = QuadImageQuery(self.initial_image)
        divided_query.divisions = self.divisions + 1
        divided_query.quad_image = QuadImage(self.initial_image, self.divisions + 1)

        return divided_query

    def set_divisions(self, count):
        self.quad_image = QuadImage(self.initial_image, count)
        self.divisions = count


class Node:
    def is_terminal(self):
        raise NotImplementedError("Need to know if terminal or not")

    # returns the parent of the child node
    def add_child(self, new_child: QuadImageQuery):
        raise NotImplementedError("Need to implement adding children")

    def find(self, target: QuadImageQuery):
        raise NotImplementedError("Need to implement finding child")


class TerminalNode(Node):
    def __init__(self, quadimage: QuadImage, full_res_image: np.ndarray):
        self.quad_image = quadimage
        self.term_full_res_image = full_res_image
        self.terminal_data = None

    def is_terminal(self):
        return True

    def set_terminal_data(self, terminal_data):
        self.terminal_data = terminal_data

    def get_terminal_data(self):
        return self.terminal_data


class BranchingNode(Node):
    def __init__(self, quadimage: QuadImage):
        self.quad_image = quadimage
        self.children = []  # list of branching or terminal nodes

    def is_terminal(self):
        return False

    def find(self, target: QuadImageQuery):
        for child in self.children:
            if target.quad_image == child.quad_image:
                if not child.is_terminal():
                    divided = target.divided()
                    found, location = child.find(divided)
                    if found:
                        # exact match has been found, return true and location
                        return True, location
                    else:
                        # no exact match found, return closest branching node
                        return False, location
                else:
                    return True, self

        # not in any of the children, this is the "deepest" location of the search
        return False, self

    def add_child(self, new_child: QuadImageQuery):
        assert (
            new_child.quad_image.divisions == self.quad_image.divisions + 1
        ), f"New child has divisions: {new_child.quad_image.divisions} but should be {self.quad_image.divisions + 1}"

        for index, child in enumerate(self.children):
            if new_child.quad_image == child.quad_image:
                divided = new_child.divided()
                if not child.is_terminal():
                    assert (
                        divided.quad_image.divisions == child.quad_image.divisions + 1
                    ), f"Adding child with {divided.quad_image.divisions} divisions to parent with {child.quad_image.divisions} divisions"
                    return child.add_child(divided)
                else:
                    # Create branching node, have "self" be a child of this branching node, have "new_child" be a child of this branching node
                    # might need to maintain a reference to a parent for this
                    new_branching = BranchingNode(child.quad_image)
                    original_divisions = child.quad_image.divisions

                    origin_clone = QuadImageQuery(child.term_full_res_image)
                    origin_clone.set_divisions(original_divisions)
                    original = origin_clone.divided()
                    assert (
                        new_branching.quad_image.divisions == child.quad_image.divisions
                    ), ""
                    assert (
                        origin_clone.quad_image.divisions == child.quad_image.divisions
                    ), "bruh"
                    assert (
                        original.quad_image.divisions
                        == new_branching.quad_image.divisions + 1
                    ), f"Original divisions: {original.quad_image.divisions}, New_branching divisions: {new_branching.quad_image.divisions}, self divisions: {self.quad_image.divisions}"
                    assert (
                        divided.quad_image.divisions
                        == new_branching.quad_image.divisions + 1
                    ), f"divided divisions: {divided.quad_image.divisions}, New_branching divisions: {new_branching.quad_image.divisions}"
                    new_branching.add_child(original)
                    new_branching.add_child(divided)
                    self.children[index] = new_branching
                    assert (
                        self.children[index].quad_image.divisions
                        == self.quad_image.divisions + 1
                    )
                    return self.children[index]

        new_child_node = TerminalNode(new_child.quad_image, new_child.initial_image)
        assert new_child_node.quad_image.divisions == self.quad_image.divisions + 1

        self.children.append(new_child_node)
        return self


import cv2
import os
import argparse

root_img = RootImg()
root = BranchingNode(root_img)

parser = argparse.ArgumentParser(description="Fuzzy reverse image searching")
parser.add_argument(
    "source_dir",
    metavar="s",
    type=str,
    help="directory containing files to search against",
)

args = parser.parse_args()

plain_paths = os.listdir(args.source_dir)
for plain_path in plain_paths:
    plain = cv2.imread(os.path.join(args.source_dir, plain_path))
    plainImg = QuadImageQuery(plain)
    assert plainImg.quad_image.divisions == 0
    root.add_child(plainImg)
    print(f"Inserted: {args.source_dir}")

path = input()
while path != "":
    noise = cv2.imread(path)
    noiseImg = QuadImageQuery(noise)
    found, loc = root.find(noiseImg)
    print(
        f"Found: \t\t{path}"
        if found
        else f"Not Found:\t{path}, nearest: {len(loc.children)}"
    )
    path = input()
