## This makefile fragment allows building KiCAD modules out of SVG files, and
## would typically be used as a command line quicky:
##
##    make -f svg2mod.mk example.kicad_mod
##
## Or when included in a makefile, this will define a pattern rule for generating
## KiCAD modules from SVG sources.

## The path and common arguments
SVG2MOD_PY = $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/svg2mod/svg2mod.py
SVG2MOD_ARGS = --format pretty --precision 1.0
FACTOR ?= 1.0

## The pattern rule to turn any SVG into a KiCAD footprint.
%.kicad_mod: %.svg
	$(SVG2MOD_PY) $(SVG2MOD_ARGS) --factor $(FACTOR) \
		-i $< -o $@ --name $(*F) --value $(*F)
