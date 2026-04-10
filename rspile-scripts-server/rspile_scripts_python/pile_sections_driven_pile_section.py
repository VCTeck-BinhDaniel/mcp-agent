import inspect
import os

from RSPileScripting.enums import *
from RSPileScripting.RSPileModeler import RSPileModeler
from RSPileScripting.Utilities.ColorPicker import ColorPicker

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
RSPileModeler.startApplication(60044)

rspile_modeler = RSPileModeler(60044)
model = rspile_modeler.openFile(rf"{current_dir}\example_models\DrivenPile.rspile2")

pile_section_list = model.getPileSections()

pile_section1 = pile_section_list[0]
pile_section2 = pile_section_list[1]

pile_section1.setName("Timber Pile Section")
pile_section1.setColor(ColorPicker.Rose)
pile_section1.DrivenCapacity.setCrossSectionType(DrivenCrossSectionType.TIMBER_PILE)
pile_section1.DrivenCapacity.Timber.setDiameterOfPile(0.6)

pile_section2.setName("H Pile Section")
pile_section2.setColor(ColorPicker.Gold)
pile_section2.DrivenCapacity.RolledSection.setDesignation(
    PileSectionDesignation.HP360_x_132
)

print(pile_section1.getName())
print(ColorPicker.getColorName(pile_section1.getColor()))
print(pile_section1.DrivenCapacity.getCrossSectionType())
print(pile_section1.DrivenCapacity.Timber.getDiameterOfPile())

print(pile_section2.getName())
print(ColorPicker.getColorName(pile_section2.getColor()))
print(pile_section2.DrivenCapacity.getCrossSectionType())
print(pile_section2.DrivenCapacity.RolledSection.getShape())
print(pile_section2.DrivenCapacity.RolledSection.getType())
print(pile_section2.DrivenCapacity.RolledSection.getDesignation())

model.save()
model.close()

rspile_modeler.closeApplication()
