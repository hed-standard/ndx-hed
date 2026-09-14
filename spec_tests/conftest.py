# The hed-tests submodule carries its own unit tests (for its maintenance scripts). They are not
# ours to run, so pytest must not collect them when it is pointed at spec_tests/.
collect_ignore = ["hed-tests"]
