import inspect
import os

from RSPileScripting.enums import *
from RSPileScripting.RSPileModeler import RSPileModeler
from RSPileScripting.Utilities.ColorPicker import ColorPicker

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
RSPileModeler.startApplication(60044)

rspile_modeler = RSPileModeler(60044)
model = rspile_modeler.openFile(rf"{current_dir}\example_models\DrivenPile.rspile2")

pile_section_list = model.getPileTypes()

pile_type1 = pile_section_list[0]

pile_type1.setName("Driven Pile Type 1")
pile_type1.setColor(ColorPicker.Indigo)
pile_type1.Driven.Sections.setCrossSectionType(DrivenPileTypeCrossSection.TAPERED)
pile_type1.Driven.Sections.setTaperAngle(0.3)
pile_type1.Driven.Sections.setPileSegmentsByLength(1.2, [["Timber Pile Section", 20]])

print(pile_type1.getName())
print(ColorPicker.getColorName(pile_type1.getColor()))
print(pile_type1.Driven.Sections.getCrossSectionType())
print(pile_type1.Driven.Sections.getTaperAngle())
print(pile_type1.Driven.Sections.getPileSegmentsByLength())

model.save()
model.close()

rspile_modeler.closeApplication()
