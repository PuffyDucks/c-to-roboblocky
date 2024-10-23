class block_data:
    def __init__(self, type, dropdown=False):
        self.type = type
        self.dropdown = dropdown

block_names = {
    "line": block_data("draw_line", dropdown=True),
    "randInt": block_data("math_random_int")
}