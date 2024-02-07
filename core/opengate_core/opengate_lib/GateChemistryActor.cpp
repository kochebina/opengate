/* --------------------------------------------------
   Copyright (C): OpenGATE Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   ------------------------------------ -------------- */

#include "GateChemistryActor.h"

#include <G4EventManager.hh>
#include <G4DNAChemistryManager.hh>
#include <G4EmDNAChemistry_option3.hh>

#include "GateHelpersDict.h"

#include "../g4_bindings/chemistryadaptator.h"

GateChemistryActor::GateChemistryActor(pybind11::dict &user_info):
	GateVActor(user_info, true)
{
  fActions.insert("NewStage");

  auto timeStepModelStr = DictGetStr(user_info, "timestep_model");
	auto timeStepModel = fIRT;
	if(timeStepModelStr == "IRT")           timeStepModel = fIRT;
	else if(timeStepModelStr == "SBS")      timeStepModel = fSBS;
	else if(timeStepModelStr == "IRT_syn")  timeStepModel = fIRT_syn;
	else /* TODO error; detect Python-side? */;

	auto* chemistryList = ChemistryAdaptator<G4EmDNAChemistry_option3>::getChemistryList();
	if(chemistryList != nullptr)
		chemistryList->SetTimeStepModel(timeStepModel);
}

void GateChemistryActor::NewStage() {
	auto* stackManager = G4EventManager::GetEventManager()->GetStackManager();
	if(stackManager != nullptr && stackManager->GetNTotalTrack() == 0) {
		G4DNAChemistryManager::Instance()->Run();
	}
}
