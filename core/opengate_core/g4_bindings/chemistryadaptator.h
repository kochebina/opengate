/* --------------------------------------------------
   Copyright (C): OpenGATE Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   -------------------------------------------------- */

#ifndef chemistryadaptator_h
#define chemistryadaptator_h

class G4DNAMolecularReactionTable;

template<typename C>
class ChemistryAdaptator: public C {
public:
	ChemistryAdaptator(int verbosity) {
		C::SetVerboseLevel(verbosity);
		_chemistryLists.push_back(this);
	}

	void ConstructTimeStepModel(G4DNAMolecularReactionTable* reactionTable) override {
		C::ConstructTimeStepModel(reactionTable);
	}

	static C* getChemistryList() {
		for(auto* chemistryList: _chemistryLists) {
			auto* ptr = dynamic_cast<C*>(chemistryList);
			if(ptr != nullptr) return ptr;
		}
		return nullptr;
	}

private:
	inline static std::vector<G4VUserChemistryList*> _chemistryLists;
};

#endif
