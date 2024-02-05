/* --------------------------------------------------
   Copyright (C): OpenGATE Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   ------------------------------------ -------------- */

#include "GateChemistryActor.h"

#include <G4DNAChemistryManager.hh>

GateChemistryActor::GateChemistryActor(pybind11::dict &user_info):
	GateVActor(user_info)
{
  fActions.insert("NewStage");
}

void GateChemistryActor::NewStage() {
	std::ofstream of{"/tmp/chem", std::ios_base::app};
	of << "+ NewStage\n";

	G4cout << "+++ NewStage" << G4endl;

	// if(stackManager->GetNTotalTrack() == 0) {
		// G4DNAChemistryManager::Instance()->Run();
	// }
}
