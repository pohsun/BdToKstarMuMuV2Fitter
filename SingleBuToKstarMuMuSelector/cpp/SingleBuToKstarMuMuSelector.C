// vim: sw=4 ts=4 fdm=marker et:

// -----------------------------------------------
//       Author: Xin Shi <Xin.Shi@cern.ch> 
//       Created:   <2013-02-26 Tue 12:08> 
// -----------------------------------------------
#define SingleBuToKstarMuMuSelector_cxx

#include <iostream>
#include <sstream>
#include <map>
#include "SingleBuToKstarMuMuSelector.h"
#include <TH2.h>
#include <TStyle.h>
#include <TProof.h>
#include <TVector3.h>
#include <TLorentzVector.h>

// Global Constants
constexpr double B_MASS = 5.279;
constexpr double KSTAR_MASS = 0.89166;
constexpr double KSTAR_WIDTH = 0.0508;
constexpr double MUON_MASS = 0.10565837;
constexpr double KAON_MASS = 0.493677;
constexpr double PION_MASS = 0.13957018;
constexpr double KSHORT_MASS = 0.497614;
constexpr int BIGNUMBER = 9999;

// user defined variables
int   Run;
int   Event;

float Q2           ;
float Bmass        ;
float CosThetaL    ;
float CosThetaK    ;
float Phi          ;

int   Triggers     ;
float Mumumass     ;
float Mumumasserr  ;
float Kstarmass    ;
float Kshortmass   ;

int   nB           ;
int   BIndex;  // Index in multicandidate ntuple
int   Bchg         ;
float Bpt          ;
float Beta         ;
float Bphi         ;
float Bvtxcl       ;
float Blxysig      ;
float Bcosalphabs  ;
float Bcosalphabs2d;
float Bctau        ;

float Kshortpt     ;
float Pippt        ;
float Pipeta       ;
float Pipphi       ;
float Pimpt        ;
float Pimeta       ;
float Pimphi       ;
float Trkpt        ;
float Trkdcasigbs  ;

float Dimupt      ;
float Dimueta     ;
float Dimuphi     ;

// Branches for Generator level information
float genQ2        ;
float genCosThetaL ;
float genCosThetaK ;
float genPhi       ;

int   genBChg      ;
float genBPt       ;
float genBEta      ;
float genBPhi      ;
float genBVtxX     ;
float genBVtxY     ;
float genBVtxZ     ;

float genKstPt     ;
float genKstEta    ;
float genKstPhi    ;
int   genTkChg     ;
float genTkPt      ;
float genTkEta     ;
float genTkPhi     ;
float genKPt       ;//Could be K+-/Kshort
float genKEta      ;
float genKPhi      ;
float genKVtxX     ;
float genKVtxY     ;
float genKVtxZ     ;
float genPipPt     ;//pion pair decayed from Kshort
float genPipEta    ;
float genPipPhi    ;
float genPimPt     ;
float genPimEta    ;
float genPimPhi    ;

float genDimuPt    ;
float genDimuEta   ;
float genDimuPhi   ;
float genMupPt     ;
float genMupEta    ;
float genMupPhi    ;
float genMumPt     ;
float genMumEta    ;
float genMumPhi    ;

bool isTrueB;
bool isTrueMum;
bool isTrueMup;
bool isTrueK;  // Could be K+-/Kshort
bool isTrueKst;

void ResetEventContent()
{//{{{
    Run            = -1;
    Event          = -1;

    Q2             = 0;
    Bmass          = 0;
    CosThetaL      = BIGNUMBER;
    CosThetaK      = BIGNUMBER;
    Phi            = BIGNUMBER;

    Triggers       = 0;
    Mumumass       = 0;
    Mumumasserr    = 0;
    Kstarmass      = 0;
    Kshortmass     = 0;

    nB             = 0;
    BIndex         = -1;
    Bpt            = 0;
    Beta           = 0;
    Bphi           = 0;
    Bchg           = 0;
    Bvtxcl         = 0;
    Blxysig        = 0;
    Bcosalphabs    = 0;
    Bcosalphabs2d  = 0;
    Bctau          = 0;

    Kshortpt       = 0;
    Pimpt          = 0;
    Pippt          = 0;
    Pimeta         = 0;
    Pipeta         = 0;
    Pimphi         = 0;
    Pipphi         = 0;
    Trkpt          = 0;
    Trkdcasigbs    = 0;

    Dimupt         = 0;
    Dimueta        = 0;
    Dimuphi        = 0;

    // mc
    genBChg = BIGNUMBER;
    genBPt = 0;
    genBEta= 0;
    genBPhi= 0;
    genBVtxX = 0;
    genBVtxY = 0;
    genBVtxZ = 0;
    genMupPt = 0;
    genMupEta= 0;
    genMupPhi= 0;
    genMumPt = 0;
    genMumEta= 0;
    genMumPhi= 0;

    genDimuPt = 0;
    genDimuEta = 0;
    genDimuPhi = 0;

    genKstPt = 0;
    genKstEta= 0;
    genKstPhi= 0;
    genTkChg = BIGNUMBER;
    genTkPt = 0;
    genTkEta= 0;
    genTkPhi= 0;
    genKPt = 0;//Could be K+-/Kshort
    genKEta= 0;
    genKPhi= 0;
    genKVtxX = 0;
    genKVtxY = 0;
    genKVtxZ = 0;
    genPipPt = 0;//pion pair decayed from Kshort
    genPipEta= 0;
    genPipPhi= 0;
    genPimPt = 0;
    genPimEta= 0;
    genPimPhi= 0;
    genQ2 = 0;
    genCosThetaL = BIGNUMBER;
    genCosThetaK = BIGNUMBER;
    genPhi       = BIGNUMBER;

    isTrueB = false;
    isTrueMum = false;
    isTrueMup = false;
    isTrueK = false;
    isTrueKst = false;
}//}}}

void str_replace(std::string& str, const std::string& oldStr, const std::string& newStr)
{//{{{
  size_t pos = 0;
  while((pos = str.find(oldStr, pos)) != std::string::npos)
  {
    str.replace(pos, oldStr.length(), newStr);
    pos += newStr.length();
  }
}//}}}

string get_option_value(string option, string name, string defaultVal="")
{//{{{
  vector<string> args;
  istringstream f(option);
  string s;    
  while (getline(f, s, ';')) {
    args.push_back(s);
  }
  
  string value; 
  int found = -1;
  for(vector<string>::iterator it = args.begin(); it != args.end(); ++it) {
    value = *it; 
    found = value.find(name);
    if (found == 0) {
      str_replace(value, name+"=", ""); 
      break; 
    }
  }
  if (found == 0){
      return value; 
  }else{
      return defaultVal;
  }

}//}}}

void SingleBuToKstarMuMuSelector::Begin(TTree * /*tree*/)
{//{{{
    printf(" ---------- Begin Job ---------- \n");
    string option = GetOption();
    eventContent = get_option_value(option, "eventContent", "data");
    cutSet = get_option_value(option, "cutSet", "default"); 
    isMC = get_option_value(option, "isMC", "false") == "true" ? true : false;
    ofilename = get_option_value(option, "ofilename", "sel.root"); 
}//}}}

void SingleBuToKstarMuMuSelector::SlaveBegin(TTree * /*tree*/)
{//{{{
    fOutputTree_ = new TTree("tree", "Single candidate tree indexed with Run:Event.");
    fOutputTree_->Branch("Run"      , &Run);
    fOutputTree_->Branch("Event"    , &Event);

    if (!isOFriendTree){
        // Minimal for fit
        fOutputTree_->Branch("Q2"            , &Q2            , "Q2/F");
        fOutputTree_->Branch("Bmass"         , &Bmass         , "Bmass/F");
        fOutputTree_->Branch("CosThetaL"     , &CosThetaL     , "CosThetaL/F");
        fOutputTree_->Branch("CosThetaK"     , &CosThetaK     , "CosThetaK/F");
        fOutputTree_->Branch("Phi"           , &Phi           , "Phi/F");

        fOutputTree_->Branch("Triggers"      , &Triggers      , "Triggers/I");
        fOutputTree_->Branch("Mumumass"      , &Mumumass      , "Mumumass/F");
        fOutputTree_->Branch("Mumumasserr"   , &Mumumasserr   , "Mumumasserr/F");
        fOutputTree_->Branch("Kstarmass"     , &Kstarmass     , "Kstarmass/F");
        fOutputTree_->Branch("Kshortmass"    , &Kshortmass    , "Kshortmass/F");

        // Minimal for optimization and optimized cut
        fOutputTree_->Branch("nB"            , &nB            , "Nb/I");
        fOutputTree_->Branch("BIndex"        , &BIndex        , "BIndex/I");
        fOutputTree_->Branch("Bchg"          , &Bchg          , "Bchg/I");
        fOutputTree_->Branch("Bpt"           , &Bpt           , "Bpt/F");
        fOutputTree_->Branch("Beta"          , &Beta          , "Beta/F");
        fOutputTree_->Branch("Bphi"          , &Bphi          , "Bphi/F");
        fOutputTree_->Branch("Bvtxcl"        , &Bvtxcl        , "Bvtxcl/F");
        fOutputTree_->Branch("Blxysig"       , &Blxysig       , "Blxysig/F");
        fOutputTree_->Branch("Bcosalphabs"   , &Bcosalphabs   , "Bcosalphabs/F");
        fOutputTree_->Branch("Bcosalphabs2d" , &Bcosalphabs2d , "Bcosalphabs2d/F");
        fOutputTree_->Branch("Bctau"         , &Bctau         , "Bctau/F");

        fOutputTree_->Branch("Kshortpt"      , &Kshortpt      , "Kshortpt/F");
        fOutputTree_->Branch("Pimpt"         , &Pimpt         , "Pimpt/F");
        fOutputTree_->Branch("Pimeta"        , &Pimeta        , "Pimeta/F");
        fOutputTree_->Branch("Pimphi"        , &Pimphi        , "Pimphi/F");
        fOutputTree_->Branch("Pippt"         , &Pippt         , "Pippt/F");
        fOutputTree_->Branch("Pipeta"        , &Pipeta        , "Pipeta/F");
        fOutputTree_->Branch("Pipphi"        , &Pipphi        , "Pipphi/F");
        fOutputTree_->Branch("Trkpt"         , &Trkpt         , "Trkpt/F");
        fOutputTree_->Branch("Trkdcasigbs"   , &Trkdcasigbs   , "Trkdcasigbs/F");

        fOutputTree_->Branch("Dimupt"        , &Dimupt        , "Dimupt/F");
        fOutputTree_->Branch("Dimueta"       , &Dimueta       , "Dimueta/F");
        fOutputTree_->Branch("Dimuphi"       , &Dimuphi       , "Dimuphi/F");
    }

    std::map<string, int> mapcontent;
    mapcontent.insert(std::pair<string, int>("data", 1));
    mapcontent.insert(std::pair<string, int>("mc", 999));
    if (mapcontent.find(eventContent) == mapcontent.end()){
        printf("ERROR\t: No compatible datatype found. Please check use following types...\n\t\t[");
        for (auto iContent = mapcontent.begin(); iContent != mapcontent.end(); iContent++){
            if (iContent->second != 0) printf("%s,",iContent->first.c_str());
        }
        printf("]\n");
        throw "Unknown eventContent";
    }
    switch (mapcontent[eventContent]) {
        case 1:
            break;
        case 999:
            fOutputTree_->Branch("genBChg"      , &genBChg      , "genBChg/I");
            fOutputTree_->Branch("genBPt"       , &genBPt       , "genBPt/F");
            fOutputTree_->Branch("genBEta"      , &genBEta      , "genBEta/F");
            fOutputTree_->Branch("genBPhi"      , &genBPhi      , "genBPhi/F");
            fOutputTree_->Branch("genBVtxX"     , &genBVtxX     , "genBVtxX/F");
            fOutputTree_->Branch("genBVtxY"     , &genBVtxY     , "genBVtxY/F");
            fOutputTree_->Branch("genBVtxZ"     , &genBVtxZ     , "genBVtxZ/F");
            fOutputTree_->Branch("genMupPt"     , &genMupPt     , "genMupPt/F");
            fOutputTree_->Branch("genMupEta"    , &genMupEta    , "genMupEta/F");
            fOutputTree_->Branch("genMupPhi"    , &genMupPhi    , "genMupPhi/F");
            fOutputTree_->Branch("genMumPt"     , &genMumPt     , "genMumPt/F");
            fOutputTree_->Branch("genMumEta"    , &genMumEta    , "genMumEta/F");
            fOutputTree_->Branch("genMumPhi"    , &genMumPhi    , "genMumPhi/F");

	        fOutputTree_->Branch("genDimuPt"    , &genDimuPt    , "genDimuPt/F");
            fOutputTree_->Branch("genDimuEta"   , &genDimuEta   , "genDimuEta/F");
            fOutputTree_->Branch("genDimuPhi"   , &genDimuPhi   , "genDimuPhi/F");

            fOutputTree_->Branch("genKstPt"     , &genKstPt     , "genKstPt/F");
            fOutputTree_->Branch("genKstEta"    , &genKstEta    , "genKstEta/F");
            fOutputTree_->Branch("genKstPhi"    , &genKstPhi    , "genKstPhi/F");
            fOutputTree_->Branch("genTkChg"     , &genTkChg     , "genTkChg/I");
            fOutputTree_->Branch("genTkPt"      , &genTkPt      , "genTkPt/F");
            fOutputTree_->Branch("genTkEta"     , &genTkEta     , "genTkEta/F");
            fOutputTree_->Branch("genTkPhi"     , &genTkPhi     , "genTkPhi/F");
            fOutputTree_->Branch("genKPt"       , &genKPt       , "genKPt/F");
            fOutputTree_->Branch("genKEta"      , &genKEta      , "genKEta/F");
            fOutputTree_->Branch("genKPhi"      , &genKPhi      , "genKPhi/F");
            fOutputTree_->Branch("genKVtxX"     , &genKVtxX     , "genKVtxX/F");
            fOutputTree_->Branch("genKVtxY"     , &genKVtxY     , "genKVtxY/F");
            fOutputTree_->Branch("genKVtxZ"     , &genKVtxZ     , "genKVtxZ/F");
            fOutputTree_->Branch("genPipPt"     , &genPipPt     , "genPipPt/F");
            fOutputTree_->Branch("genPipEta"    , &genPipEta    , "genPipEta/F");
            fOutputTree_->Branch("genPipPhi"    , &genPipPhi    , "genPipPhi/F");
            fOutputTree_->Branch("genPimPt"     , &genPimPt     , "genPimPt/F");
            fOutputTree_->Branch("genPimEta"    , &genPimEta    , "genPimEta/F");
            fOutputTree_->Branch("genPimPhi"    , &genPimPhi    , "genPimPhi/F");
            fOutputTree_->Branch("genQ2"        , &genQ2        , "genQ2/F");
            fOutputTree_->Branch("genCosThetaL" , &genCosThetaL , "genCosThetaL/F");
            fOutputTree_->Branch("genCosThetaK" , &genCosThetaK , "genCosThetaK/F");
            fOutputTree_->Branch("genPhi"       , &genPhi       , "genPhi/F");

            fOutputTree_->Branch("isTrueB"      , &isTrueB      , "isTrueB/O");
            fOutputTree_->Branch("isTrueMum"    , &isTrueMum    , "isTrueMum/O");
            fOutputTree_->Branch("isTrueMup"    , &isTrueMup    , "isTrueMup/O");
            fOutputTree_->Branch("isTrueK"      , &isTrueK      , "isTrueK/O");
            fOutputTree_->Branch("isTrueKst"    , &isTrueKst    , "isTrueKst/O");
            break;
        default:
            break;
    }

    fOutput->AddAll(gDirectory->GetList()); 
}//}}}

bool SingleBuToKstarMuMuSelector::HasGoodDimuon(int i)
{//{{{
	// Not exactly the same as the official id, but it's acceptable.
    // Ref: 
    //      https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideMuonId#New_Version_recommended
    //      https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideFinalTrackSelectors
    if ( // soft muon id
        mumisgoodmuon->at(i)
        && mupisgoodmuon->at(i)
        && mumntrklayers->at(i) > 5  // 2012 Data
        && mupntrklayers->at(i) > 5  // 2012 Data
        && mumnpixlayers->at(i) > 0  // 1,0 (old,new)
        && mupnpixlayers->at(i) > 0  // 1,0 (old,new)
        && mumnormchi2->at(i) < 1.8
        && mupnormchi2->at(i) < 1.8
        && fabs(mumdxyvtx->at(i)) < 0.3  // 3,0.3 (old,new)
        && fabs(mupdxyvtx->at(i)) < 0.3  // 3,0.3 (old,new)
        && fabs(mumdzvtx->at(i)) < 20   // 30,20 (old,new)
        && fabs(mupdzvtx->at(i)) < 20   // 30,20 (old,new)
     	){
        return true;
    }
    return false;
}//}}}

int SingleBuToKstarMuMuSelector::SelectB()
{//{{{
    // Remark: Resonance rejection and anti-radiation is applied after this single candidate selection stage.
    BIndex = -1;
    nB = 0;
    double best_bvtxcl = 0.;

    if (cutSet == "default"){
        cutSet = "ANv18";
    }

    if (cutSet == "ANv18") {
        for (int i=0; i < nb; i++){//{{{
	        if (!HasGoodDimuon(i)){
                continue;
            }
            if (!(trkpt->at(i) > 0.4
                && fabs(trkdcabs->at(i)/trkdcabserr->at(i)) > 0.4
                && sqrt((kspx->at(i))*(kspx->at(i))+(kspy->at(i))*(kspy->at(i))) > 1.0
                && bvtxcl->at(i) > 0.1
                && (blsbs->at(i)/blsbserr->at(i)) > 12.
                && bcosalphabs2d->at(i) > 0.9994
                && (kstarmass->at(i) > 0.742 && kstarmass->at(i) < 1.042)
                && (bmass->at(i) > 4.5 && bmass->at(i) < 6.0 )) ){
                continue;
            }
            
            nB++;
            if (bvtxcl->at(i) > best_bvtxcl){
                best_bvtxcl = bvtxcl->at(i);
                BIndex = i;
	        }
	    } //}}}
    }else if (cutSet == "nocut"){
        nB = nb;
        for (int i = 0; i < nb; i++) {
            if (bvtxcl->at(i) > best_bvtxcl) {
                best_bvtxcl = bvtxcl->at(i); 
                BIndex = i; 
            }
        }
    }else if (cutSet == "genonly"){
		BIndex = -1;
	}else{
        throw TString::Format("Unknown cutSet %s\n", cutSet.c_str()).Data();
    }

    return BIndex;
}//}}}

void SingleBuToKstarMuMuSelector::UpdateBranchData()
{//{{{
    TLorentzVector B_4vec, Kst_4vec, Mup_4vec, Mum_4vec, Tk_4vec, K_4vec, Pip_4vec, Pim_4vec, buff1, buff2, buff3;
    B_4vec.SetXYZM(bpx->at(BIndex),bpy->at(BIndex),bpz->at(BIndex),bmass->at(BIndex));
    Kst_4vec.SetXYZM(kspx->at(BIndex)+trkpx->at(BIndex),kspy->at(BIndex)+trkpy->at(BIndex),kspz->at(BIndex)+trkpz->at(BIndex),kstarmass->at(BIndex));
    Mup_4vec.SetXYZM(muppx->at(BIndex),muppy->at(BIndex),muppz->at(BIndex),MUON_MASS);
    Mum_4vec.SetXYZM(mumpx->at(BIndex),mumpy->at(BIndex),mumpz->at(BIndex),MUON_MASS);
    Tk_4vec.SetXYZM(trkpx->at(BIndex),trkpy->at(BIndex),trkpz->at(BIndex),PION_MASS);
    K_4vec.SetXYZM(kspx->at(BIndex),kspy->at(BIndex),kspz->at(BIndex),KSHORT_MASS);
    Pip_4vec.SetXYZM(pippx->at(BIndex),pippy->at(BIndex),pippz->at(BIndex),PION_MASS);
    Pim_4vec.SetXYZM(pimpx->at(BIndex),pimpy->at(BIndex),pimpz->at(BIndex),PION_MASS);

    Q2 = pow(mumumass->at(BIndex),2);
    Bmass = bmass->at(BIndex);
    
    Triggers = triggernames->size();
    Mumumass = mumumass->at(BIndex);
    Mumumasserr = mumumasserr->at(BIndex);
    Kstarmass = kstarmass->at(BIndex);
    Kshortmass = K_4vec.Mag();

    Bchg = bchg->at(BIndex);
    Bpt = B_4vec.Pt();
    Beta = B_4vec.Eta();
    Bphi = B_4vec.Phi();
    Bvtxcl = bvtxcl->at(BIndex);
    Blxysig = (blsbs->at(BIndex)/blsbserr->at(BIndex));
    Bcosalphabs = bcosalphabs->at(BIndex);
    Bcosalphabs2d = bcosalphabs2d->at(BIndex);
    Bctau = bctau->at(BIndex);

    Kshortpt = sqrt( (kspx->at(BIndex))*(kspx->at(BIndex)) + (kspy->at(BIndex))*(kspy->at(BIndex)) );
    Pippt = Pip_4vec.Pt();
    Pipeta = Pip_4vec.Eta();
    Pipphi = Pip_4vec.Phi();
    Pimpt = Pim_4vec.Pt();
    Pimeta = Pim_4vec.Eta();
    Pimphi = Pim_4vec.Phi();
    Trkpt = trkpt->at(BIndex);
    Trkdcasigbs = fabs( trkdcabs->at(BIndex)/trkdcabserr->at(BIndex) );

    buff1 = B_4vec;
    buff2 = Mup_4vec+Mum_4vec;

    Dimupt = buff2.Pt();
    Dimueta = buff2.Eta();
    Dimuphi = buff2.Phi();

    buff1.Boost(-buff2.BoostVector());
    buff3 = Bchg > 0 ? Mum_4vec : Mup_4vec;//Take mu- to avoid extra minus sign.
    buff3.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());
    CosThetaL = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();

    buff1 = B_4vec;
    buff2 = Kst_4vec;
    buff1.Boost(-buff2.BoostVector());
    buff3 = Tk_4vec;//Take pion to avoid extra minus.
    buff3.Boost(-buff2.BoostVector());
    CosThetaK = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();

    buff1 = Tk_4vec;
    buff2 = Bchg > 0 ? Mup_4vec : Mum_4vec;
    buff1.Boost(-B_4vec.BoostVector());
    buff2.Boost(-B_4vec.BoostVector());
    auto buff1_perpB = buff1.Vect() - buff1.Vect().Dot(B_4vec.Vect())/B_4vec.Vect().Mag2() * B_4vec.Vect();
    auto buff2_perpB = buff2.Vect() - buff2.Vect().Dot(B_4vec.Vect())/B_4vec.Vect().Mag2() * B_4vec.Vect();
    Phi = buff2_perpB.Angle(buff1_perpB);
}//}}}

void SingleBuToKstarMuMuSelector::UpdateBranchMC()
{//{{{
    TLorentzVector genB_4vec, genKst_4vec, genMup_4vec, genMum_4vec, genTk_4vec, genK_4vec, genPip_4vec, genPim_4vec, buff1, buff2, buff3;
    genB_4vec   . SetXYZM(genbpx   , genbpy   , genbpz   , B_MASS);
    genMup_4vec . SetXYZM(genmuppx , genmuppy , genmuppz , MUON_MASS);
    genMum_4vec . SetXYZM(genmumpx , genmumpy , genmumpz , MUON_MASS);
    genKst_4vec . SetXYZM(genkstpx , genkstpy , genkstpz , KSTAR_MASS);
    genTk_4vec  . SetXYZM(gentrkpx , gentrkpy , gentrkpz , PION_MASS);
    genK_4vec   . SetXYZM(genkspx  , genkspy  , genkspz  , KSHORT_MASS);
    genPip_4vec . SetXYZM(genpippx , genpippy , genpippz , PION_MASS);
    genPim_4vec . SetXYZM(genpimpx , genpimpy , genpimpz , PION_MASS);

    genBChg      = genbchg;
    genBPt       = genB_4vec.Pt();
    genBEta      = genB_4vec.Eta();
    genBPhi      = genB_4vec.Phi();
    genBVtxX     = 0;//Should be at PV?
    genBVtxY     = 0;
    genBVtxZ     = 0;
    genMupPt     = genMup_4vec.Pt();
    genMupEta    = genMup_4vec.Eta();
    genMupPhi    = genMup_4vec.Phi();
    genMumPt     = genMum_4vec.Pt();
    genMumEta    = genMum_4vec.Eta();
    genMumPhi    = genMum_4vec.Phi();

    genKstPt     = genKst_4vec.Pt();
    genKstEta    = genKst_4vec.Eta();
    genKstPhi    = genKst_4vec.Phi();
    genTkChg     = gentrkchg;
    genTkPt      = genTk_4vec.Pt();
    genTkEta     = genTk_4vec.Eta();
    genTkPhi     = genTk_4vec.Phi();
    genKPt       = genK_4vec.Pt();
    genKEta      = genK_4vec.Eta();
    genKPhi      = genK_4vec.Phi();
    genKVtxX     = genksvtxx;
    genKVtxY     = genksvtxy;
    genKVtxZ     = genksvtxz;
    genPipPt     = genPip_4vec.Pt();
    genPipEta    = genPip_4vec.Eta();
    genPipPhi    = genPip_4vec.Phi();
    genPimPt     = genPim_4vec.Pt();
    genPimEta    = genPim_4vec.Eta();
    genPimPhi    = genPim_4vec.Phi();
    genQ2        = (genMup_4vec+genMum_4vec).Mag2();

    buff1 = genB_4vec;
    buff2 = genMup_4vec+genMum_4vec;

    genDimuPt = buff2.Pt();
    genDimuEta = buff2.Eta();
    genDimuPhi = buff2.Phi();

    buff1.Boost(-buff2.BoostVector());
    buff3 = genBChg > 0 ? genMum_4vec : genMup_4vec;//Take mu- to avoid extra minus sign.
    buff3.Boost(-buff2.BoostVector());
    genCosThetaL = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();

    buff1 = genB_4vec;
    buff2 = genKst_4vec;
    buff1.Boost(-genKst_4vec.BoostVector());
    buff3 = genTk_4vec;//Take pion to avoid extra minus.
    buff3.Boost(-genKst_4vec.BoostVector());
    genCosThetaK = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();
    
    buff1 = genTk_4vec;
    buff2 = genBChg > 0 ? genMup_4vec : genMum_4vec;
    buff1.Boost(-genB_4vec.BoostVector());
    buff2.Boost(-genB_4vec.BoostVector());
    auto buff1_perpB = buff1.Vect() - buff1.Vect().Dot(genB_4vec.Vect())/genB_4vec.Vect().Mag2() * genB_4vec.Vect();
    auto buff2_perpB = buff2.Vect() - buff2.Vect().Dot(genB_4vec.Vect())/genB_4vec.Vect().Mag2() * genB_4vec.Vect();
    genPhi = buff2_perpB.Angle(buff1_perpB);
}//}}}

void SingleBuToKstarMuMuSelector::UpdateGenMatch()
{//{{{
    TLorentzVector Kst_4vec, Mup_4vec, Mum_4vec, K_4vec;
    Kst_4vec . SetXYZM(kspx->at(BIndex)+trkpx->at(BIndex) , kspy->at(BIndex)+trkpy->at(BIndex) , kspz->at(BIndex)+trkpz->at(BIndex) , kstarmass->at(BIndex));
    Mup_4vec . SetXYZM(muppx->at(BIndex)              , muppy->at(BIndex)              , muppz->at(BIndex)              , MUON_MASS);
    Mum_4vec . SetXYZM(mumpx->at(BIndex)              , mumpy->at(BIndex)              , mumpz->at(BIndex)              , MUON_MASS);
    K_4vec   . SetXYZM(kspx->at(BIndex)               , kspy->at(BIndex)               , kspz->at(BIndex)               , KSHORT_MASS);

    TLorentzVector genKst_4vec, genMup_4vec, genMum_4vec, genK_4vec;
    genMup_4vec . SetXYZM(genmuppx , genmuppy , genmuppz , MUON_MASS);
    genMum_4vec . SetXYZM(genmumpx , genmumpy , genmumpz , MUON_MASS);
    genKst_4vec . SetXYZM(genkstpx , genkstpy , genkstpz , KSTAR_MASS);
    genK_4vec   . SetXYZM(genkspx  , genkspy  , genkspz  , KSHORT_MASS);

    double maxDeltaR = 0.15;
    if (Mup_4vec.DeltaR(genMup_4vec) < maxDeltaR) isTrueMup = true;
    if (Mum_4vec.DeltaR(genMum_4vec) < maxDeltaR) isTrueMum = true;
    if (K_4vec.DeltaR(genK_4vec) < maxDeltaR) isTrueK = true;
    if (isTrueK && Kst_4vec.DeltaR(genKst_4vec) < maxDeltaR) isTrueKst = true;
    if (isTrueKst && isTrueMup && isTrueMum) isTrueB = true;
}//}}}

Bool_t SingleBuToKstarMuMuSelector::Process(Long64_t entry)
{//{{{
    ResetEventContent();
    GetEntry(entry);

    Run = run;
    Event = event;
    BIndex = SelectB();
    // printf("DEBUG\t: Event %u with BIndex %d\n", event, BIndex);

    if (BIndex >= 0){
        // Fill and reset index
        UpdateBranchData();
        if (isMC){
            UpdateBranchMC();
            UpdateGenMatch();
        }
        fOutputTree_->Fill();
    }else if (isMC && cutSet == "genonly"){
        UpdateBranchMC();
        fOutputTree_->Fill();
    }

    return kTRUE;
}//}}}

void SingleBuToKstarMuMuSelector::SlaveTerminate()
{//{{{
    fOutputTree_->BuildIndex("Run", "Event");

    TFile *fOutputFile = new TFile(ofilename.c_str(), "recreate"); 
    fOutput->Write();
    fOutputFile->Close();
}//}}}

void SingleBuToKstarMuMuSelector::Terminate()
{//{{{
    printf(" ---------- End Job ---------- \n" ) ;
}//}}}
