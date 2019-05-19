#define plotMatchCandPreSelector_cxx
// vim: set sts=3 sw=3 fdm=syntax fdl=0 fdn=3 et:
// The class definition in plotMatchCandPreSelector.h has been generated automatically
// by the ROOT utility TTree::MakeSelector(). This class is derived
// from the ROOT class TSelector. For more information on the TSelector
// framework see $ROOTSYS/README/README.SELECTOR or the ROOT User Manual.


// The following methods are defined in this file:
//    Begin():        called every time a loop on the tree starts,
//                    a convenient place to create your histograms.
//    SlaveBegin():   called after Begin(), when on PROOF called only on the
//                    slave servers.
//    Process():      called for each event, in this function you decide what
//                    to read and fill your histograms.
//    SlaveTerminate: called at the end of the loop on the tree, when on PROOF
//                    called only on the slave servers.
//    Terminate():    called at the end of the loop on the tree,
//                    a convenient place to draw/fit your histograms.
//
// To use this file, try the following session on your Tree T:
//
// root> T->Process("plotMatchCandPreSelector.C")
// root> T->Process("plotMatchCandPreSelector.C","some options")
// root> T->Process("plotMatchCandPreSelector.C+")
//


#include "plotMatchCandPreSelector.h"
#include <TH2.h>
#include <TLorentzVector.h>
#include <TStyle.h>

// This looks extremely weird, but it works!
// https://stackoverflow.com/questions/8016780/undefined-reference-to-static-constexpr-char
constexpr char plotMatchCandPreSelector::cutString[];

void plotMatchCandPreSelector::Begin(TTree * /*tree*/)
{
   // The Begin() function is called at the start of the query.
   // When running with PROOF Begin() is only called on the client.
   // The tree argument is deprecated (on PROOF 0 is passed).

   TString option = GetOption();
}

void plotMatchCandPreSelector::SlaveBegin(TTree * /*tree*/)
{
   // The SlaveBegin() function is called after the Begin() function.
   // When running with PROOF SlaveBegin() is called on each slave server.
   // The tree argument is deprecated (on PROOF 0 is passed).
   TString option = GetOption();

   fOutputTree = new TTree("tree","FriendTree based on Bmass:Mumumass");
   fOutputTree->Branch("Bmass", &Bmass_oTree);
   fOutputTree->Branch("Mumumass", &Mumumass_oTree);
   fOutputTree->Branch("Kshortmass", &Kshortmass_oTree);
}

Bool_t plotMatchCandPreSelector::Process(Long64_t entry)
{
   // The Process() function is called for each entry in the tree (or possibly
   // keyed object in the case of PROOF) to be processed. The entry argument
   // specifies which entry in the currently loaded tree is to be processed.
   // When processing keyed objects with PROOF, the object is already loaded
   // and is available via the fObject pointer.
   //
   // This function should contain the \"body\" of the analysis. It can contain
   // simple or elaborate selection criteria, run algorithms on the data
   // of the event and typically fill histograms.
   //
   // The processing can be stopped by calling Abort().
   //
   // Use fStatus to set the return value of TTree::Process().
   //
   // The return value is currently not used.

   // if (fChain->GetEntryNumber(entry) < 0){
      // return kTRUE;
   // }

   fReader.SetLocalEntry(entry);
   matchNextPreSel(); // Update matchedEventNo, matchedBindex

   if (matchedBindex >= 0){
      fReader_PreSel.SetEntry(matchedEventNo);
      TLorentzVector Kshort_4vec;
      TLorentzVector Pip_4vec, Pim_4vec;
      Pip_4vec.SetXYZM(
            Pippx_PreSel->at(matchedBindex),
            Pippy_PreSel->at(matchedBindex),
            Pippz_PreSel->at(matchedBindex),
            0.13957);
      Pim_4vec.SetXYZM(
            Pimpx_PreSel->at(matchedBindex),
            Pimpy_PreSel->at(matchedBindex),
            Pimpz_PreSel->at(matchedBindex),
            0.13957);
      Kshort_4vec = Pip_4vec+Pim_4vec;
      
      Bmass_oTree = *Bmass;
      Mumumass_oTree = *Mumumass;
      Kshortmass_oTree = Kshort_4vec.M();

      // Fill and reset index
      fOutputTree->Fill();
      matchedBindex = -1;
   }

   return kTRUE;
}

void plotMatchCandPreSelector::SlaveTerminate()
{
   // The SlaveTerminate() function is called after all entries or objects
   // have been processed. When running with PROOF SlaveTerminate() is called
   // on each slave server.
   
   printf("%lld entries collected out of %lld entries.\n", fOutputTree->GetEntries(), el->GetN());
   fOutputTree->BuildIndex("Bmass", "Mumumass");


   TFile *fOutputFile = new TFile("plotMatchCandPreSelector.root","RECREATE");
   fOutputTree->Write();
   fOutputFile->Close();
}

void plotMatchCandPreSelector::Terminate()
{
   // The Terminate() function is the last function to be called during
   // a query. It always runs on the client, it can be used to present
   // the results graphically or save the results to file.

   delete el;
   el = 0;

   delete fChain_PreSel;
   fChain_PreSel = 0;
}

void plotMatchCandPreSelector::matchNextPreSel()
{
    constexpr double epsilon = 1e-5;
    for (long int iEvt_PreSel = matchedEventNo;
            iEvt_PreSel < nentries_PreSel;
            iEvt_PreSel++){
        fReader_PreSel.SetEntry(iEvt_PreSel);
        if (*Nb == 0 || *Nb != *Nb_PreSel){
            continue;
        }
        for (int iB_PreSel = 0; iB_PreSel < *Nb_PreSel; iB_PreSel++) {
            if (fabs(*Bmass-Bmass_PreSel->at(iB_PreSel)) < epsilon &&
                fabs(*Mumumass-Mumumass_PreSel->at(iB_PreSel)) < epsilon) {
                matchedEventNo = iEvt_PreSel;
                matchedBindex = iB_PreSel;
                goto exit;
            }
        }
    }
    // In case of not found.
    matchedBindex = -1;
    return;

exit:
    printf("Found matched B+ at %lld/%lld.\n", matchedEventNo, nentries_PreSel);
    return;
}
