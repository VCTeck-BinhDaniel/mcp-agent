import inspect
import os

from RSPileScripting.enums import *
from RSPileScripting.RSPileModeler import RSPileModeler
from RSPileScripting.Utilities.ColorPicker import ColorPicker

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
RSPileModeler.startApplication(60044)

rspile_modeler = RSPileModeler(60044)
model = rspile_modeler.openFile(rf"{current_dir}\example_models\HelicalPile.rspile2")

pile_section_list = model.getPileTypes()

pile_type1 = pile_section_list[0]

pile_type1.setName("Circular Concrete Pile")
pile_type1.setColor(ColorPicker.Red)
pile_type1.Helical.Sections.setPileSegmentsByLength(1.2, [["Hollow Section", 10.01]])

helices = pile_type1.Helical.Sections.Helices
helices.setHeightReductionFactor(1.4)
# add identical 9 helices at a spacing of 0.5m each
helices.setHelicesBySpacing(6, [0.3, 0.1], ([[0.3, 0.1, 0.5] for i in range(8)]))

print(pile_type1.getName())
print(ColorPicker.getColorName(pile_type1.getColor()))
print(pile_type1.Helical.Sections.getPileSegmentsByLength())
print(pile_type1.Helical.Sections.Helices.getHelicesBySpacing())

model.save()
model.close()

rspile_modeler.closeApplication()
