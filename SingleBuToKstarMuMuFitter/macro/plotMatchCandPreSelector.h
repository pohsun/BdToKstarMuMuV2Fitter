// vim: set sts=3 sw=3 fdm=syntax fdl=1 fdn=3 et:
//////////////////////////////////////////////////////////
// This class has been automatically generated on
// Wed May 15 09:22:53 2019 by ROOT version 6.16/00
// from TChain tree/
//////////////////////////////////////////////////////////

#ifndef plotMatchCandPreSelector_h
#define plotMatchCandPreSelector_h

#include <TROOT.h>
#include <TChain.h>
#include <TTree.h>
#include <TEntryList.h>
#include <TFile.h>
#include <TSelector.h>
#include <TTreeReader.h>
#include <TTreeReaderValue.h>
#include <TTreeReaderArray.h>

// Headers needed by this particular selector


class plotMatchCandPreSelector : public TSelector {
public :
   TTreeReader     fReader;  //!the tree reader for post-selector tree
   TTree           *fChain = 0;   //!pointer to the analyzed TTree or TChain
   // Readers to access the data (delete the ones you do not need).
   TTreeReaderValue<Int_t> Nb;
   TTreeReaderValue<Double_t> Bmass;
   TTreeReaderValue<Double_t> Mumumass;
   
   TTreeReader     fReader_PreSel;  //!the tree reader for pre-selector tree
   TChain          *fChain_PreSel = 0;   //!pointer to the analyzed TTree or TChain
   Long64_t       nentries_PreSel;
   // Readers to access the data (delete the ones you do not need).
   TTreeReaderValue<Int_t> Nb_PreSel;
   TTreeReaderValue<std::vector<double>> Bmass_PreSel;
   TTreeReaderValue<std::vector<double>> Mumumass_PreSel;
   TTreeReaderValue<std::vector<double>> Pippx_PreSel;
   TTreeReaderValue<std::vector<double>> Pippy_PreSel;
   TTreeReaderValue<std::vector<double>> Pippz_PreSel;
   TTreeReaderValue<std::vector<double>> Pimpx_PreSel;
   TTreeReaderValue<std::vector<double>> Pimpy_PreSel;
   TTreeReaderValue<std::vector<double>> Pimpz_PreSel;

   plotMatchCandPreSelector(TTree * /*tree*/ =0) :
      Nb(fReader, "Nb"),
      Bmass(fReader, "Bmass"),
      Mumumass(fReader, "Mumumass"),
      Nb_PreSel(fReader_PreSel, "nb"),
      Bmass_PreSel(fReader_PreSel, "bmass"),
      Mumumass_PreSel(fReader_PreSel, "mumumass"),
      Pippx_PreSel(fReader_PreSel, "pippx"),
      Pippy_PreSel(fReader_PreSel, "pippy"),
      Pippz_PreSel(fReader_PreSel, "pippz"),
      Pimpx_PreSel(fReader_PreSel, "pimpx"),
      Pimpy_PreSel(fReader_PreSel, "pimpy"),
      Pimpz_PreSel(fReader_PreSel, "pimpz")
   {
   }
   virtual ~plotMatchCandPreSelector() { }
   virtual Int_t   Version() const { return 2; }
   virtual void    Begin(TTree *tree);
   virtual void    SlaveBegin(TTree *tree);
   virtual void    Init(TTree *tree);
   virtual Bool_t  Notify();
   virtual Bool_t  Process(Long64_t entry);
   virtual Int_t   GetEntry(Long64_t entry, Int_t getall = 0) { return fChain ? fChain->GetTree()->GetEntry(entry, getall) : 0; }
   virtual void    SetOption(const char *option) { fOption = option; }
   virtual void    SetObject(TObject *obj) { fObject = obj; }
   virtual void    SetInputList(TList *input) { fInput = input; }
   virtual TList  *GetOutputList() const { return fOutput; }
   virtual void    SlaveTerminate();
   virtual void    Terminate();
   
   // User-defined variable and functions
   Long64_t matchedEventNo;
   Int_t matchedBindex;
   TEntryList *el; // Keep a record of good events.
   static constexpr char cutString[] = "(Triggers>=1)&&(Kstarmass>0.792 && Kstarmass < 0.992)&&((Mumumass > 3.096916+3.5*Mumumasserr || Mumumass < 3.096916-5.5*Mumumasserr) && (Mumumass > 3.686109+3.5*Mumumasserr || Mumumass < 3.686109-3.5*Mumumasserr))&&(abs(Bmass-Mumumass-2.182)>0.09 && abs(Bmass-Mumumass-1.593)>0.03)&&(Mumumass>1&&Mumumass<19)";
   void matchNextPreSel(); // Match with Nb, Bmass, Mumumass
      // Output contents
   TTree *fOutputTree = 0;
   double Bmass_oTree;
   double Mumumass_oTree;
   double Kshortmass_oTree;

   ClassDef(plotMatchCandPreSelector,0);

};

#endif

#ifdef plotMatchCandPreSelector_cxx
void plotMatchCandPreSelector::Init(TTree *tree)
{
   // The Init() function is called when the selector needs to initialize
   // a new tree or chain. Typically here the reader is initialized.
   // It is normally not necessary to make changes to the generated
   // code, but the routine can be extended by the user if needed.
   // Init() will be called many times when running on PROOF
   // (once per file to be processed).

   el = new TEntryList("el", "");
   fChain = tree;
   fChain->Draw(">>el", cutString, "entrylist");
   printf("%lld selected events in total.\n", el->GetN());
   fChain->SetEntryList(el);

   fReader.SetTree(tree); // Don't use SetTree(tree, el), unable to remove Tree changing warnings.
   

   fChain_PreSel = new TChain("tree");
   fChain_PreSel->Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/ntp/v3p2/BuToKstarMuMu-data-2012*-v3p2-merged.root");

   // See https://root-forum.cern.ch/t/using-ttreereader-with-tchain/27279
   nentries_PreSel = fChain_PreSel->GetEntries();
   fChain_PreSel->LoadTree(0);

   fReader_PreSel.SetTree(fChain_PreSel);

   matchedEventNo = 0;
}

Bool_t plotMatchCandPreSelector::Notify()
{
   // The Notify() function is called when a new file is opened. This
   // can be either for a new TTree in a TChain or when when a new TTree
   // is started when using PROOF. It is normally not necessary to make changes
   // to the generated code, but the routine can be extended by the
   // user if needed. The return value is currently not used.

   return kTRUE;
}


#endif // #ifdef plotMatchCandPreSelector_cxx
