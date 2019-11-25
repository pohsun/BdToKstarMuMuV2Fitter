// vim: set sts=4 sw=4 fdm=syntax fdl=0 fdl=2 et:
//
#include "EvtGenBase/EvtComplex.hh"
#include "EvtGenBase/EvtTensor4C.hh"
#include "EvtGenBase/EvtVector4C.hh"
#include "EvtGenBase/EvtVector4R.hh"
#include "EvtGenBase/EvtVectorParticle.hh"
#include "EvtGenBase/EvtDiracSpinor.hh"
#include "EvtGenBase/EvtParticle.hh"
#include "EvtGenBase/EvtKine.hh"
#include "EvtGenBase/EvtGammaMatrix.hh"
#include "EvtGenBase/EvtRandom.hh"
#include "EvtGenBase/EvtRandomEngine.hh"
#include "EvtGenBase/EvtDecayTable.hh"
#include "EvtGenBase/EvtReport.hh"
#include "EvtGenBase/EvtPDL.hh"
#include "EvtGenBase/EvtStdHep.hh"
#include "EvtGenBase/EvtSecondary.hh"
#include "EvtGenBase/EvtConst.hh"
#include "EvtGen/EvtGen.hh"
#include "EvtGenBase/EvtParticleFactory.hh"
#include "EvtGenBase/EvtStdlibRandomEngine.hh"
#include "EvtGenBase/EvtIdSet.hh"
#include "EvtGenBase/EvtParser.hh"

#include "EvtGenBase/EvtAbsRadCorr.hh"
#include "EvtGenBase/EvtDecayBase.hh"

#ifdef EVTGEN_EXTERNAL
#include "EvtGenExternal/EvtExternalGenList.hh"
#endif

#include <cstdio>
#include <fstream>
#include <sstream>
#include <cmath>
#include <string>
#include <vector>
#include <cstdlib>

#include "TH1.h"
#include "TH2.h"
#include "TFile.h"
#include "TApplication.h"
#include "TROOT.h"
#include "TTree.h"
#include "TLorentzVector.h"
#include "TRandom3.h"

using std::vector;

void runKstarll(int nevent,EvtGen& myGenerator);
void runKstarJpsi(int nevent, EvtGen& myGenerator);

int main(int argc, char* argv[]){

  EvtRandomEngine* myRandomEngine = new EvtStdlibRandomEngine();

  if (!TROOT::Initialized()) {
    static TROOT root("RooTuple", "RooTuple ROOT in EvtGen");
  }
  if (argc==1){

    EvtVector4R p(0.0,1.0,0.0,0.0);
    EvtVector4R k(0.0,0.0,1.0,0.0);

    EvtTensor4C T=dual(EvtGenFunctions::directProd(p,k));

    report(INFO,"EvtGen") << "p:"<<p<<std::endl;
    report(INFO,"EvtGen") << "k:"<<k<<std::endl;
    report(INFO,"EvtGen") << "T=dual(directProd(p,k)):"<<T<<std::endl;
    report(INFO,"EvtGen") << "T03:"<<T.get(0,3)<<std::endl;
    return 1;
  }

  EvtAbsRadCorr* radCorrEngine = 0;
  std::list<EvtDecayBase*> extraModels;

#ifdef EVTGEN_EXTERNAL
  EvtExternalGenList genList;
  radCorrEngine = genList.getPhotosModel();
  extraModels = genList.getListOfModels();
#endif

  // EvtGen myGenerator("DECAY_NOLONGLIFE.DEC", "evt.pdl", myRandomEngine, radCorrEngine, &extraModels);
  EvtGen myGenerator("DECAY_2010.DEC", "evt.pdl", myRandomEngine, radCorrEngine, &extraModels);


  if (!strcmp(argv[1],"kstarll")) {
    int nevent=atoi(argv[2]);
    runKstarll(nevent, myGenerator);
  }

  if (!strcmp(argv[1],"kstarjpsi")) {
    int nevent=atoi(argv[2]);
    runKstarJpsi(nevent, myGenerator);
  }

  delete myRandomEngine;
  return 0;

}

void runKstarll(int nevent, EvtGen &myGenerator) {
    int     genBChg      = 999;
    double  genBPt       = 0;
    double  genBEta      = 0;
    double  genBPhi      = 0;
    double  genBVtxX     = 0;
    double  genBVtxY     = 0;
    double  genBVtxZ     = 0;
    double  genMupPt     = 0;
    double  genMupEta    = 0;
    double  genMupPhi    = 0;
    double  genMumPt     = 0;
    double  genMumEta    = 0;
    double  genMumPhi    = 0;
    double  genKstPt     = 0;
    double  genKstEta    = 0;
    double  genKstPhi    = 0;
    int     genTkChg     = 999;
    double  genTkPt      = 0;
    double  genTkEta     = 0;
    double  genTkPhi     = 0;
    double  genKPt       = 0;//Could be K+-/Kshort
    double  genKEta      = 0;
    double  genKPhi      = 0;
    double  genKVtxX     = 0;
    double  genKVtxY     = 0;
    double  genKVtxZ     = 0;
    double  genPipPt     = 0;//pion pair decayed from Kshort
    double  genPipEta    = 0;
    double  genPipPhi    = 0;
    double  genPimPt     = 0;
    double  genPimEta    = 0;
    double  genPimPhi    = 0;
    double  genQ2        = 0;
    double  genCosThetaL = 999;
    double  genCosThetaK = 999;

    TFile *file=new TFile("BuToKstarMuMu_NoFilter_E.root", "RECREATE");
    TTree *tree_ = new TTree("tree","tree");
    tree_->Branch("genBChg"      , &genBChg      , "genBChg/I"); 
    tree_->Branch("genBPt"       , &genBPt       , "genBPt/D"); 
    tree_->Branch("genBEta"      , &genBEta      , "genBEta/D"); 
    tree_->Branch("genBPhi"      , &genBPhi      , "genBPhi/D"); 
    tree_->Branch("genBVtxX"     , &genBVtxX     , "genBVtxX/D"); 
    tree_->Branch("genBVtxY"     , &genBVtxY     , "genBVtxY/D"); 
    tree_->Branch("genBVtxZ"     , &genBVtxZ     , "genBVtxZ/D"); 
    tree_->Branch("genMupPt"     , &genMupPt     , "genMupPt/D"); 
    tree_->Branch("genMupEta"    , &genMupEta    , "genMupEta/D"); 
    tree_->Branch("genMupPhi"    , &genMupPhi    , "genMupPhi/D"); 
    tree_->Branch("genMumPt"     , &genMumPt     , "genMumPt/D"); 
    tree_->Branch("genMumEta"    , &genMumEta    , "genMumEta/D"); 
    tree_->Branch("genMumPhi"    , &genMumPhi    , "genMumPhi/D"); 
    tree_->Branch("genKstPt"     , &genKstPt     , "genKstPt/D"); 
    tree_->Branch("genKstEta"    , &genKstEta    , "genKstEta/D"); 
    tree_->Branch("genKstPhi"    , &genKstPhi    , "genKstPhi/D"); 
    tree_->Branch("genTkChg"     , &genTkChg     , "genTkChg/I"); 
    tree_->Branch("genTkPt"      , &genTkPt      , "genTkPt/D"); 
    tree_->Branch("genTkEta"     , &genTkEta     , "genTkEta/D"); 
    tree_->Branch("genTkPhi"     , &genTkPhi     , "genTkPhi/D"); 
    tree_->Branch("genKPt"       , &genKPt       , "genKPt/D"); 
    tree_->Branch("genKEta"      , &genKEta      , "genKEta/D"); 
    tree_->Branch("genKPhi"      , &genKPhi      , "genKPhi/D"); 
    tree_->Branch("genKVtxX"     , &genKVtxX     , "genKVtxX/D"); 
    tree_->Branch("genKVtxY"     , &genKVtxY     , "genKVtxY/D"); 
    tree_->Branch("genKVtxZ"     , &genKVtxZ     , "genKVtxZ/D"); 
    tree_->Branch("genPipPt"     , &genPipPt     , "genPipPt/D"); 
    tree_->Branch("genPipEta"    , &genPipEta    , "genPipEta/D"); 
    tree_->Branch("genPipPhi"    , &genPipPhi    , "genPipPhi/D"); 
    tree_->Branch("genPimPt"     , &genPimPt     , "genPimPt/D"); 
    tree_->Branch("genPimEta"    , &genPimEta    , "genPimEta/D"); 
    tree_->Branch("genPimPhi"    , &genPimPhi    , "genPimPhi/D"); 
    tree_->Branch("genQ2"        , &genQ2        , "genQ2/D"); 
    tree_->Branch("genCosThetaL" , &genCosThetaL , "genCosThetaL/D"); 
    tree_->Branch("genCosThetaK" , &genCosThetaK , "genCosThetaK/D"); 

    static EvtId UPS4=EvtPDL::getId(std::string("Upsilon(4S)"));
    static EvtId B0=EvtPDL::getId(std::string("B0"));
    static EvtId Bu=EvtPDL::getId(std::string("B+"));
    static EvtId Bubar=EvtPDL::getId(std::string("B-"));

    int count=1;

    EvtVector4R b,kstar,l1,l2,k,trk,pip,pim;

    char udecay_name[100];
    strcpy(udecay_name,"Bu_Kstarmumu_Kspi.dec"); //all B+/- decays to K*+/- mu mu

    myGenerator.readUDecay(udecay_name);

    //K*mm  
    int n=9;
    std::vector<double> q2low(n);
    std::vector<double> q2high(n);
    std::vector<int> counts(n);
    q2low[0]=0.0;     q2high[0]=1.0;
    q2low[1]=1.0;     q2high[1]=2.0;
    q2low[2]=2.0;     q2high[2]=4.3;
    q2low[3]=4.3;     q2high[3]=8.68;
    q2low[4]=8.68;    q2high[4]=10.09;
    q2low[5]=10.09;   q2high[5]=12.86;
    q2low[6]=12.86;   q2high[6]=14.18;
    q2low[7]=14.18;   q2high[7]=16.00;
    q2low[8]=16.00;   q2high[8]=19.00;

    TRandom3 rnd;
    rnd.SetSeed();
    do{
        //EvtVector4R p_init(EvtPDL::getMass(Bu),0.0,0.0,0.0);
        // Randomized production rate in phi
        double motherP = 10.;
        double motherPx, motherPy, motherPz;
        rnd.Sphere(motherPx, motherPy, motherPz, motherP);
        EvtVector4R p_init(sqrt(pow(EvtPDL::getMass(Bu),2)+100.), motherPx, motherPy, motherPz);// Allowed to give some extra boost.

        EvtParticle* root_part=0;
        if (count < nevent/2){
            root_part = EvtParticleFactory::particleFactory(Bu, p_init);
        }else{
            root_part = EvtParticleFactory::particleFactory(Bubar, p_init);
        }
        root_part->setDiagonalSpinDensity();      

        myGenerator.generateDecay(root_part);
        //root_part->printTree();
        //root_part->getDaug(0)->printTree();
        //root_part->getDaug(1)->printTree();
        //root_part->getDaug(2)->printTree();

        b=root_part->getP4Lab();
        if ( root_part->getPDGId() > 0 ){
            l1=root_part->getDaug(1)->getP4Lab();
            l2=root_part->getDaug(2)->getP4Lab();
        }else{
            l1=root_part->getDaug(2)->getP4Lab();
            l2=root_part->getDaug(1)->getP4Lab();
        }
        kstar=root_part->getDaug(0)->getP4Lab();
        k=root_part->getDaug(0)->getDaug(0)->getP4Lab();
        trk=root_part->getDaug(0)->getDaug(1)->getP4Lab();
        pip=root_part->getDaug(0)->getDaug(0)->getDaug(0)->getP4Lab();
        pim=root_part->getDaug(0)->getDaug(0)->getDaug(1)->getP4Lab();

        double qsq=(l1+l2).mass2();
        if (qsq > 19) continue;

        TLorentzVector genMup_4vec, genMum_4vec;
        genMup_4vec.SetXYZM(l1.get(1)    , l1.get(2)    , l1.get(3)   , l1.mass());
        genMum_4vec.SetXYZM(l2.get(1)    , l2.get(2)    , l2.get(3)   , l2.mass());

        // PtEtaFilter, if B is static, you have almost no chance to pass the filter.
        //printf("Mu+ Pt is %f GeV\n",genMup_4vec.Pt());
        //if (genMum_4vec.Pt()  <  2.8) continue;
        //if (genMup_4vec.Pt()  <  2.8) continue;
        //if (genMum_4vec.Eta() >  2.3) continue;
        //if (genMup_4vec.Eta() >  2.3) continue;
        //if (genMum_4vec.Eta() < -2.3) continue;
        //if (genMup_4vec.Eta() < -2.3) continue;

        count++;
        for (int j=0;j<n;j++){
            if (qsq>q2low[j] && qsq<q2high[j]) counts[j]++;
        }

        //Fill all tree stuff
        TLorentzVector genB_4vec, genKst_4vec, genTk_4vec, genK_4vec, genPip_4vec, genPim_4vec, buff1, buff2, buff3;
        genB_4vec.SetXYZM(b.get(1)       , b.get(2)     , b.get(3)    , b.mass());
        genKst_4vec.SetXYZM(kstar.get(1) , kstar.get(2) , kstar.get(3), kstar.mass());
        genTk_4vec.SetXYZM(trk.get(1)    , trk.get(2)   , trk.get(3)  , trk.mass());
        genK_4vec.SetXYZM(k.get(1)       , k.get(2)     , k.get(3)    , k.mass());
        genPip_4vec.SetXYZM(pip.get(1)   , pip.get(2)   , pip.get(3)  , pip.mass());
        genPim_4vec.SetXYZM(pim.get(1)   , pim.get(2)   , pim.get(3)  , pim.mass());
        
        genBChg      = root_part->getPDGId()/abs(root_part->getPDGId());
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
        genTkChg     = root_part->getPDGId()/abs(root_part->getPDGId());
        genTkPt      = genTk_4vec.Pt();
        genTkEta     = genTk_4vec.Eta();
        genTkPhi     = genTk_4vec.Phi();
        genKPt       = genK_4vec.Pt();
        genKEta      = genK_4vec.Eta();
        genKPhi      = genK_4vec.Phi();
        genKVtxX     = 0;//Set to 0 in EvtGen
        genKVtxY     = 0;
        genKVtxZ     = 0;
        genPipPt     = genPip_4vec.Pt();
        genPipEta    = genPip_4vec.Eta();
        genPipPhi    = genPip_4vec.Phi();
        genPimPt     = genPim_4vec.Pt();
        genPimEta    = genPim_4vec.Eta();
        genPimPhi    = genPim_4vec.Phi();
        
        genQ2        = (genMup_4vec+genMum_4vec).Mag2();
        buff1 = genB_4vec;
        buff2 = genMup_4vec+genMum_4vec;
        buff1.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());
        if (root_part->getPDGId() > 0){
            buff3 = genMum_4vec;//Take mu- to avoid extra minus sign.
        }else{
            buff3 = genMup_4vec;//Take mu+ to avoid extra minus sign.
        }
        buff3.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());
        genCosThetaL = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();
        
        buff1 = genB_4vec;
        buff2 = genKst_4vec;
        buff1.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());
        buff3 = genTk_4vec;//Take pion to avoid extra minus.
        buff3.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());
        genCosThetaK = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();
        
        tree_->Fill();
        root_part->deleteTree();
        // report(INFO,"EvtGen") << "count:" << count-1 <<" "<<(l1+l2).mass2()<<std::endl;
    }while ( count <= nevent);
  
    for (int j=0;j<n;j++){
        std::cout << "["<<q2low[j]<<".."<<q2high[j]<<"]="<<counts[j]<<std::endl;
    }

    file->Write();
    file->Close();
    report(INFO,"EvtGen") << "SUCCESS\n";
  
}

void runKstarJpsi(int nevent, EvtGen &myGenerator) {
    int     genBChg      = 999;
    double  genBPt       = 0;
    double  genBEta      = 0;
    double  genBPhi      = 0;
    double  genBVtxX     = 0;
    double  genBVtxY     = 0;
    double  genBVtxZ     = 0;
    double  genMupPt     = 0;
    double  genMupEta    = 0;
    double  genMupPhi    = 0;
    double  genMumPt     = 0;
    double  genMumEta    = 0;
    double  genMumPhi    = 0;
    double  genKstPt     = 0;
    double  genKstEta    = 0;
    double  genKstPhi    = 0;
    int     genTkChg     = 999;
    double  genTkPt      = 0;
    double  genTkEta     = 0;
    double  genTkPhi     = 0;
    double  genKPt       = 0;//Could be K+-/Kshort
    double  genKEta      = 0;
    double  genKPhi      = 0;
    double  genKVtxX     = 0;
    double  genKVtxY     = 0;
    double  genKVtxZ     = 0;
    double  genPipPt     = 0;//pion pair decayed from Kshort
    double  genPipEta    = 0;
    double  genPipPhi    = 0;
    double  genPimPt     = 0;
    double  genPimEta    = 0;
    double  genPimPhi    = 0;
    double  genQ2        = 0;
    double  genCosThetaL = 999;
    double  genCosThetaK = 999;

    TFile *file=new TFile("BuToKstarJpsi_NoFilter_E.root", "RECREATE");
    TTree *tree_ = new TTree("tree","tree");
    tree_->Branch("genBChg"      , &genBChg      , "genBChg/I"); 
    tree_->Branch("genBPt"       , &genBPt       , "genBPt/D"); 
    tree_->Branch("genBEta"      , &genBEta      , "genBEta/D"); 
    tree_->Branch("genBPhi"      , &genBPhi      , "genBPhi/D"); 
    tree_->Branch("genBVtxX"     , &genBVtxX     , "genBVtxX/D"); 
    tree_->Branch("genBVtxY"     , &genBVtxY     , "genBVtxY/D"); 
    tree_->Branch("genBVtxZ"     , &genBVtxZ     , "genBVtxZ/D"); 
    tree_->Branch("genMupPt"     , &genMupPt     , "genMupPt/D"); 
    tree_->Branch("genMupEta"    , &genMupEta    , "genMupEta/D"); 
    tree_->Branch("genMupPhi"    , &genMupPhi    , "genMupPhi/D"); 
    tree_->Branch("genMumPt"     , &genMumPt     , "genMumPt/D"); 
    tree_->Branch("genMumEta"    , &genMumEta    , "genMumEta/D"); 
    tree_->Branch("genMumPhi"    , &genMumPhi    , "genMumPhi/D"); 
    tree_->Branch("genKstPt"     , &genKstPt     , "genKstPt/D"); 
    tree_->Branch("genKstEta"    , &genKstEta    , "genKstEta/D"); 
    tree_->Branch("genKstPhi"    , &genKstPhi    , "genKstPhi/D"); 
    tree_->Branch("genTkChg"     , &genTkChg     , "genTkChg/I"); 
    tree_->Branch("genTkPt"      , &genTkPt      , "genTkPt/D"); 
    tree_->Branch("genTkEta"     , &genTkEta     , "genTkEta/D"); 
    tree_->Branch("genTkPhi"     , &genTkPhi     , "genTkPhi/D"); 
    tree_->Branch("genKPt"       , &genKPt       , "genKPt/D"); 
    tree_->Branch("genKEta"      , &genKEta      , "genKEta/D"); 
    tree_->Branch("genKPhi"      , &genKPhi      , "genKPhi/D"); 
    tree_->Branch("genKVtxX"     , &genKVtxX     , "genKVtxX/D"); 
    tree_->Branch("genKVtxY"     , &genKVtxY     , "genKVtxY/D"); 
    tree_->Branch("genKVtxZ"     , &genKVtxZ     , "genKVtxZ/D"); 
    tree_->Branch("genPipPt"     , &genPipPt     , "genPipPt/D"); 
    tree_->Branch("genPipEta"    , &genPipEta    , "genPipEta/D"); 
    tree_->Branch("genPipPhi"    , &genPipPhi    , "genPipPhi/D"); 
    tree_->Branch("genPimPt"     , &genPimPt     , "genPimPt/D"); 
    tree_->Branch("genPimEta"    , &genPimEta    , "genPimEta/D"); 
    tree_->Branch("genPimPhi"    , &genPimPhi    , "genPimPhi/D"); 
    tree_->Branch("genQ2"        , &genQ2        , "genQ2/D"); 
    tree_->Branch("genCosThetaL" , &genCosThetaL , "genCosThetaL/D"); 
    tree_->Branch("genCosThetaK" , &genCosThetaK , "genCosThetaK/D"); 

    static EvtId UPS4=EvtPDL::getId(std::string("Upsilon(4S)"));
    static EvtId B0=EvtPDL::getId(std::string("B0"));
    static EvtId Bu=EvtPDL::getId(std::string("B+"));
    static EvtId Bubar=EvtPDL::getId(std::string("B-"));

    int count=1;

    EvtVector4R b,kstar,l1,l2,k,trk,pip,pim;

    char udecay_name[100];
    strcpy(udecay_name,"Bu_JpsiKstar_mumuKpi_cc.dec"); //all B+/- decays to K*+/- Jpsi
    //EvtGen myGenerator(decay_name,pdttable_name,myRandomEngine);

    myGenerator.readUDecay(udecay_name);

    //K*mm  
    int n=9;
    std::vector<double> q2low(n);
    std::vector<double> q2high(n);
    std::vector<int> counts(n);
    q2low[0]=0.0;     q2high[0]=1.0;
    q2low[1]=1.0;     q2high[1]=2.0;
    q2low[2]=2.0;     q2high[2]=4.3;
    q2low[3]=4.3;     q2high[3]=8.68;
    q2low[4]=8.68;    q2high[4]=10.09;
    q2low[5]=10.09;   q2high[5]=12.86;
    q2low[6]=12.86;   q2high[6]=14.18;
    q2low[7]=14.18;   q2high[7]=16.00;
    q2low[8]=16.00;   q2high[8]=19.00;

    TRandom3 rnd;
    rnd.SetSeed();
    do{
        double motherP = 10.;
        double motherPx, motherPy, motherPz;
        rnd.Sphere(motherPx, motherPy, motherPz, motherP);
        EvtVector4R p_init(sqrt(pow(EvtPDL::getMass(Bu),2)+100.), motherPx, motherPy, motherPz);// Allowed to give some extra boost.

        EvtParticle* root_part=0;
        if (count < nevent/2){
            root_part = EvtParticleFactory::particleFactory(Bu, p_init);
        }else{
            root_part = EvtParticleFactory::particleFactory(Bubar, p_init);
        }
        root_part->setDiagonalSpinDensity();      

        myGenerator.generateDecay(root_part);
        //root_part->printTree();
        //root_part->getDaug(0)->printTree();
        //root_part->getDaug(1)->printTree();
        //root_part->getDaug(2)->printTree();

        b=root_part->getP4Lab();
        if ( root_part->getPDGId() > 0 ){
            l1=root_part->getDaug(0)->getDaug(0)->getP4Lab();
            l2=root_part->getDaug(0)->getDaug(1)->getP4Lab();
        }else{
            l2=root_part->getDaug(0)->getDaug(0)->getP4Lab();
            l1=root_part->getDaug(0)->getDaug(1)->getP4Lab();
        }
        kstar=root_part->getDaug(1)->getP4Lab();
        k=root_part->getDaug(1)->getDaug(0)->getP4Lab();
        trk=root_part->getDaug(1)->getDaug(1)->getP4Lab();
        pip=root_part->getDaug(1)->getDaug(0)->getDaug(0)->getP4Lab();
        pim=root_part->getDaug(1)->getDaug(0)->getDaug(1)->getP4Lab();

        double qsq=(l1+l2).mass2();
        bool isGoodEvent = true;
        if (qsq > 19 || qsq < 1) isGoodEvent = false;
        if (isGoodEvent){


            count++;
            for (int j=0;j<n;j++){
                if (qsq>q2low[j] && qsq<q2high[j]) counts[j]++;
            }

            //Fill all tree stuff
            TLorentzVector genB_4vec, genKst_4vec, genTk_4vec, genK_4vec, genPip_4vec, genPim_4vec, buff1, buff2, buff3;
            TLorentzVector genMup_4vec, genMum_4vec;
            genB_4vec.SetXYZM(b.get(1)       , b.get(2)     , b.get(3)    , b.mass());
            genKst_4vec.SetXYZM(kstar.get(1) , kstar.get(2) , kstar.get(3), kstar.mass());
            genTk_4vec.SetXYZM(trk.get(1)    , trk.get(2)   , trk.get(3)  , trk.mass());
            genK_4vec.SetXYZM(k.get(1)       , k.get(2)     , k.get(3)    , k.mass());
            genPip_4vec.SetXYZM(pip.get(1)   , pip.get(2)   , pip.get(3)  , pip.mass());
            genPim_4vec.SetXYZM(pim.get(1)   , pim.get(2)   , pim.get(3)  , pim.mass());
            genMup_4vec.SetXYZM(l1.get(1)    , l1.get(2)    , l1.get(3)   , l1.mass());
            genMum_4vec.SetXYZM(l2.get(1)    , l2.get(2)    , l2.get(3)   , l2.mass());
            
            genBChg      = root_part->getPDGId()/abs(root_part->getPDGId());
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
            genTkChg     = root_part->getPDGId()/abs(root_part->getPDGId());
            genTkPt      = genTk_4vec.Pt();
            genTkEta     = genTk_4vec.Eta();
            genTkPhi     = genTk_4vec.Phi();
            genKPt       = genK_4vec.Pt();
            genKEta      = genK_4vec.Eta();
            genKPhi      = genK_4vec.Phi();
            genKVtxX     = 0;//Set to 0 in EvtGen
            genKVtxY     = 0;
            genKVtxZ     = 0;
            genPipPt     = genPip_4vec.Pt();
            genPipEta    = genPip_4vec.Eta();
            genPipPhi    = genPip_4vec.Phi();
            genPimPt     = genPim_4vec.Pt();
            genPimEta    = genPim_4vec.Eta();
            genPimPhi    = genPim_4vec.Phi();
            
            genQ2        = (genMup_4vec+genMum_4vec).Mag2();
            buff1 = genB_4vec;
            buff2 = genMup_4vec+genMum_4vec;
            buff1.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());
            if (root_part->getPDGId() > 0){
                buff3 = genMum_4vec;//Take mu- to avoid extra minus sign.
            }else{
                buff3 = genMup_4vec;//Take mu+ to avoid extra minus sign.
            }
            buff3.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());
            genCosThetaL = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();
            
            buff1 = genB_4vec;
            buff2 = genKst_4vec;
            buff1.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());
            buff3 = genTk_4vec;//Take pion to avoid extra minus.
            buff3.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());
            genCosThetaK = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();
        
            tree_->Fill();
        }

        root_part->deleteTree();
        // report(INFO,"EvtGen") << "count:" << count-1 <<" "<<(l1+l2).mass2()<<std::endl;
    }while ( count <= nevent);
  
    for (int j=0;j<n;j++){
        std::cout << "["<<q2low[j]<<".."<<q2high[j]<<"]="<<counts[j]<<std::endl;
    }

    file->Write();
    file->Close();
    report(INFO,"EvtGen") << "SUCCESS\n";
  
}
