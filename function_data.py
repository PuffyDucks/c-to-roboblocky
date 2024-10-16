class block_data:
    def __init__(self, block_type, dropdown=False):
        self.block_type = block_type
        self.dropdown = dropdown

block_names = {
    "line": block_data("draw_line", dropdown=True)
}