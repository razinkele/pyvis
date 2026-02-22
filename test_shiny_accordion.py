"""
Quick test to verify Shiny example accordion syntax is correct
"""

from shiny import App, ui, render

# Minimal test of accordion structure
app_ui = ui.page_fluid(
    ui.h2("Accordion Test"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.accordion(
                ui.accordion_panel(
                    "Section 1",
                    ui.input_text("text1", "Text Input"),
                ),
                ui.accordion_panel(
                    "Section 2",
                    ui.input_slider("slider1", "Slider", 0, 10, 5),
                ),
                ui.accordion_panel(
                    "Section 3",
                    ui.input_checkbox("check1", "Checkbox", True),
                ),
                id="test_accordion",
                open=["Section 1", "Section 2"],
                multiple=True
            ),
        ),
        ui.output_text("result")
    )
)

def server(input, output, session):
    @render.text
    def result():
        return f"Text: {input.text1()}, Slider: {input.slider1()}, Checkbox: {input.check1()}"

app = App(app_ui, server)

if __name__ == "__main__":
    print("Testing accordion structure...")
    print("If this runs, the accordion syntax is correct!")
    print("Visit http://localhost:8888")
    app.run(port=8888)
