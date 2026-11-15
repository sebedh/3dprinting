# Regenerate the printable parts from rack_minipc.py.
# Override FreeCAD if needed:  make FREECAD=freecadcmd
APPIMAGE := $(firstword $(wildcard FreeCAD*.AppImage))
ifneq ($(APPIMAGE),)
FREECAD ?= ./$(APPIMAGE) --appimage-extract-and-run freecadcmd
else
FREECAD ?= freecadcmd
endif

OUT := rack_minipc_left.stl rack_minipc_right.stl rack_minipc_left.step rack_minipc_right.step

.PHONY: all clean
all: $(OUT)

$(OUT) &: rack_minipc.py
	$(FREECAD) rack_minipc.py > build.log 2>&1 || { cat build.log; exit 1; }
	@if grep -q Traceback build.log; then cat build.log; rm -f $(OUT); exit 1; fi
	@grep -E 'RackMiniPC|slots' build.log

clean:
	rm -f $(OUT) rack_minipc.FCStd build.log
