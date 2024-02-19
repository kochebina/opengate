/* --------------------------------------------------
   Copyright (C): OpenGATE Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   ------------------------------------ -------------- */

#include "GateChemistryActor.h"

#include <CLHEP/Units/SystemOfUnits.h>
#include <G4DNAMolecularReactionTable.hh>
#include <G4EmDNAPhysics_option3.hh>
#include <G4EventManager.hh>
#include <G4DNAChemistryManager.hh>
#include <G4EmDNAChemistry_option3.hh>
#include <G4THitsMap.hh>
#include <G4MoleculeCounter.hh>
#include <G4UnitsTable.hh>
#include <G4Scheduler.hh>
#include <pybind11/pybind11.h>

#include "GateHelpersDict.h"

#include "../g4_bindings/chemistryadaptator.h"
#include "GateVActor.h"

GateChemistryActor::GateChemistryActor(pybind11::dict &user_info):
	GateVActor(user_info, true)
{
  fActions.insert("NewStage");
  fActions.insert("EndOfRunAction");
  fActions.insert("EndOfEventAction");
  fActions.insert("SteppingAction");
  fActions.insert("EndSimulationAction");

	G4MoleculeCounter::Instance()->Use();
	G4MolecularConfiguration::PrintAll();

  auto timeStepModelStr = DictGetStr(user_info, "timestep_model");
	auto timeStepModel = fIRT;
	if(timeStepModelStr == "IRT")           timeStepModel = fIRT;
	else if(timeStepModelStr == "SBS")      timeStepModel = fSBS;
	else if(timeStepModelStr == "IRT_syn")  timeStepModel = fIRT_syn;
	else /* TODO error; detect Python-side? */;

	// TODO user defined
	G4Scheduler::Instance()->SetEndTime(1 * CLHEP::microsecond);
	setTimeBinCount(50);

	{
		struct ReactionInput {
			std::vector<std::string> reactants;
			std::vector<std::string> products;
			std::string fix;
			double rate;
			int type;
		};

		std::vector<ReactionInput> reactions;
		reactions.push_back(ReactionInput{{"H", "H"}, {"H2"}, "fix", 0.503e10, 0});
		reactions.push_back(ReactionInput{{"e_aq", "H"}, {"H2", "OHm"}, "fix", 2.50e10, 0});
		reactions.push_back(ReactionInput{{"e_aq", "e_aq"}, {"H2", "OHm", "OHm"}, "fix", 0.636e10, 0});
		reactions.push_back(ReactionInput{{"H3Op", "OHm"}, {"H2O"}, "fix", 1.13e11, 0});

		reactions.push_back(ReactionInput{{"OH", "H"}, {"H2O"}, "fix", 1.55e10, 1});
		reactions.push_back(ReactionInput{{"OH", "OH"}, {"H2O2"}, "fix", 0.55e10, 1});
		reactions.push_back(ReactionInput{{"e_aq", "OH"}, {"OHm"}, "fix", 2.95e10, 1});
		reactions.push_back(ReactionInput{{"e_aq", "H2O2"}, {"OHm", "OH"}, "fix", 1.10e10, 1});
		reactions.push_back(ReactionInput{{"e_aq", "H3Op"}, {"H", "H2O"}, "fix", 2.11e10, 1});

		auto constructReactionTable = [reactions = std::move(reactions)](G4DNAMolecularReactionTable* reactionTable) {
			reactionTable->Reset();

			for(auto const& reaction: reactions) {
				double rate = reaction.rate * (1e-3 * CLHEP::m3 / (CLHEP::mole * CLHEP::s));
				auto* reactionData = new G4DNAMolecularReactionData(rate, reaction.reactants[0], reaction.reactants[1]);
				for(auto const& product: reaction.products)
					if(product != "H2O")
						reactionData->AddProduct(product);
				reactionData->ComputeEffectiveRadius();
				reactionData->SetReactionType(reaction.type);

				reactionTable->SetReaction(reactionData);
			}

			reactionTable->PrintTable();
		};

		ChemistryAdaptator<G4EmDNAChemistry_option3>::setConstructReactionTableHook(constructReactionTable);
	}

	auto* chemistryList = ChemistryAdaptator<G4EmDNAChemistry_option3>::getChemistryList();
	if(chemistryList != nullptr)
		chemistryList->SetTimeStepModel(timeStepModel);

	G4MoleculeCounter::Instance()->ResetCounter();
	G4DNAChemistryManager::Instance()->ResetCounterWhenRunEnds(false);
}

void GateChemistryActor::Initialize(G4HCofThisEvent* hce) {
	GateVActor::Initialize(hce);

	G4MoleculeCounter::Instance()->ResetCounter();
}

void GateChemistryActor::EndSimulationAction() {
}

void GateChemistryActor::EndOfRunAction(G4Run const*) {
	G4cout << "************ EndOfRun *******" << G4endl;
	for(auto [species, map]: _speciesInfoPerTime) {
		for(auto [time, data]: map) {
			G4cout << species->GetName() << " @ " << time << ": "
				<< data.number << ", " << data.g << ", " << data.sqG << G4endl;
		}
	}
}

void GateChemistryActor::EndOfEventAction(G4Event const*) {
	auto* molecularCounter = G4MoleculeCounter::Instance();

	G4cout << "____ edep: " << _edepSum << G4endl;

	if(not G4EventManager::GetEventManager()->GetConstCurrentEvent()->IsAborted()) {
		auto species = molecularCounter->GetRecordedMolecules();
		if(species && !species->empty()) {
			for(auto const* molecule: *species) {
				auto& speciesInfo = _speciesInfoPerTime[molecule];

				for(auto time: _timesToRecord) {
					auto nbMol = molecularCounter->GetNMoleculesAtTime(molecule, time);

					if(nbMol < 0) {
						G4cerr << "Invalid molecule count: " << nbMol << " < 0 " << G4endl;
						G4Exception("", "N < 0", FatalException, "");
					}

					double gValue = (nbMol / (_edepSum / CLHEP::eV)) * 100.;

					auto& molInfo = speciesInfo[time];
					molInfo.number += nbMol;
					molInfo.g += gValue;
					molInfo.sqG += gValue * gValue;
				}
			}
		} else
			G4cout << "************* No molecule recorded, edep = " << G4BestUnit(_edepSum, "Energy") << G4endl;
	}

	++_nbEvents;
  _edepSum = 0.;
	molecularCounter->ResetCounter();
}

void GateChemistryActor::SteppingAction(G4Step* step) {
	auto edep = step->GetTotalEnergyDeposit();
	if(edep <= 0.) return;

	edep *= step->GetPreStepPoint()->GetWeight();
	_edepSum += edep;
}

void GateChemistryActor::NewStage() {
	auto* stackManager = G4EventManager::GetEventManager()->GetStackManager();
	if(stackManager != nullptr && stackManager->GetNTotalTrack() == 0) {
		G4DNAChemistryManager::Instance()->Run();
	}
}

void GateChemistryActor::setTimeBinCount(int n) {
	double timeMin = 1 * CLHEP::ps;
	double timeMax = G4Scheduler::Instance()->GetEndTime() - 1 * CLHEP::ps;
	double timeMinLog = std::log10(timeMin);
	double timeMaxLog = std::log10(timeMax);
	double timeStepLog = (timeMaxLog - timeMinLog) / (n-1);

	_timesToRecord.clear();
	for(int i = 0; i < n; ++i)
		_timesToRecord.insert(std::pow(10, timeMinLog + i * timeStepLog));
}

pybind11::list GateChemistryActor::getTimes() const {
  pybind11::list o;
	std::for_each(std::begin(_timesToRecord), std::end(_timesToRecord), [&o](auto const& v) { o.append(v); });
	return o;
}

pybind11::dict GateChemistryActor::getData() const {
  pybind11::dict o;
	for(auto const& [species, map]: _speciesInfoPerTime) {
		pybind11::dict dMolecule;

		py::list count;
		py::list g;
		py::list sqG;

		for(auto const& [time, data]: map) { // time order is guaranteed by std::map
			count.append(data.number);
			g.append(data.g);
			sqG.append(data.sqG);
		}

		dMolecule["count"] = count;
		dMolecule["g"] = g;
		dMolecule["sqG"] = sqG;

		o[species->GetName()] = dMolecule;
	}

	return o;
}
