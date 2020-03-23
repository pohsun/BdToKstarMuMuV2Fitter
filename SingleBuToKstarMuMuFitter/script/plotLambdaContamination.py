#!/usr/bin/env python

import ROOT

import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
from SingleBuToKstarMuMuFitter.plotCollection import Plotter as Plotter

cimp_Define_LambdaMass = """
const float MUON_MASS = 0.10566;
const float PION_MASS = 0.13957018;
const float PROTON_MASS = 0.938272;
float Define_LambdaMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi){
    TLorentzVector proton, pion;
    proton.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PROTON_MASS);
    pion.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    if (proton.P() < pion.P()){
        proton.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PROTON_MASS);
        pion.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    }
    return (proton+pion).Mag();
}
float Define_KshortMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi){
    TLorentzVector pip, pim;
    pim.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    pip.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    return (pim+pip).Mag();
}
float Define_KstarMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi, float Trkpt, float Trketa, float Trkphi){
    TLorentzVector pip, pim, trk;
    pim.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    pip.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    trk.SetPtEtaPhiM(Trkpt, Trketa, Trkphi, PION_MASS);
    return (pim+pip+trk).Mag();
}
float Define_LambdaBMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi, float Dimupt, float Dimueta, float Dimuphi, float Mumumass){
    TLorentzVector proton, pion;
    proton.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PROTON_MASS);
    pion.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    if (proton.P() < pion.P()){
        proton.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PROTON_MASS);
        pion.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    }
    TLorentzVector dimu;
    dimu.SetPtEtaPhiM(Dimupt, Dimueta, Dimuphi, Mumumass);
    return (proton+pion+dimu).Mag();
}
"""
ROOT.gInterpreter.Declare(cimp_Define_LambdaMass)

if __name__ == '__main__':

    tree = ROOT.TChain("tree")
    for f in dataCollection.dataReaderCfg['ifile']:
        tree.Add(f)
    df = ROOT.RDataFrame(tree)\
        .Filter(anaSetup.q2bins['summary']['cutString'])\
        .Filter(anaSetup.bMassRegions['Fit']['cutString'])\
        .Filter(anaSetup.cut_passTrigger)\
        .Filter(anaSetup.cut_kshortWindow)\
        .Filter(anaSetup.cut_kstarMassWindow)\
        .Filter(anaSetup.cut_resonanceRej)\
        .Filter(anaSetup.cut_antiRadiation)\
        .Alias("LambdaMass", "Lambdamass")\
        .Define("KshortMass", "Define_KshortMass(Pippt, Pipeta, Pipphi, Pimpt, Pimeta, Pimphi)")\
        .Define("KstarMass", "Define_KstarMass(Pippt, Pipeta, Pipphi, Pimpt, Pimeta, Pimphi, Trkpt, Trketa, Trkphi)")\
        .Define("LambdaBMass", "Define_LambdaBMass(Pippt, Pipeta, Pipphi, Pimpt, Pimeta, Pimphi, Dimupt, Dimueta, Dimuphi, Mumumass)")
        #.Define("LambdaMass", "Define_LambdaMass(Pippt, Pipeta, Pipphi, Pimpt, Pimeta, Pimphi)")\
    df_LambdaSR = df.Filter("LambdaMass>1.11 && LambdaMass<1.125")
    df_vetoLambdaSR = df.Filter("LambdaMass<1.11 || LambdaMass>1.125")
    df_Lambda1330 = df.Filter("LambdaMass>1.32 && LambdaMass<1.34")
    df_vetoLambda1330 = df.Filter("LambdaMass<1.32 || LambdaMass>1.34")
    hists = {}
    hists['h_LambdaMass_bin0'] = {
        'hist': df.Histo1D(("h_LambdaMass_bin0", "", 30, 1.0, 1.3), "LambdaMass"),
        'xTitle': "m_{p#pi} [GeV]"
    }
    hists['h_LambdaMass_SR_bin0'] = {
        'hist': df.Filter(anaSetup.bMassRegions['SR']['cutString']).Histo1D(("h_LambdaMass_SR_bin0", "", 30, 1.0, 1.3), "LambdaMass"),
        'xTitle': "m_{p#pi} [GeV]"
    }
    hists['h_LambdaMass_SB_bin0'] = {
        'hist': df.Filter(anaSetup.bMassRegions['SB']['cutString']).Histo1D(("h_LambdaMass_SB_bin0", "", 30, 1.0, 1.3), "LambdaMass"),
        'xTitle': "m_{p#pi} [GeV]"
    }
    hists['h_LambdaBMass_LambdaSR_bin0'] = {
        'hist': df_LambdaSR.Histo1D(("h_LambdaBMass_LambdaSR_bin0", "", 26, 4.76, 5.80), "LambdaBMass"),
        'xTitle': "m_{#Lambda#pi#mu#mu} [GeV]"}
    hists['h_KshortMass_Lambda1p3x_bin0'] = {
        'hist': df_Lambda1330.Histo1D(("h_KshortMass_Lambda1p3x_bin0", "", 30, 0.468, 0.528), "KshortMass"),
        'xTitle': "m_{#pi#pi} [GeV]"}
    hists['h_KshortMass_VetoLambda1p3x_bin0'] = {
        'hist': df_vetoLambda1330.Histo1D(("h_KshortMass_VetoLambda1p3x_bin0", "", 30, 0.468, 0.528), "KshortMass"),
        'xTitle': "m_{#pi#pi} [GeV]"}
    hists['h_KshortMass_SR_bin0'] = {
        'hist': df.Filter(anaSetup.bMassRegions['SR']['cutString']).Histo1D(("h_KshortMass_SR_bin0", "", 30, 0.468, 0.528), "KshortMass"),
        'xTitle': "m_{#pi#pi} [GeV]"}
    hists['h_KshortMass_SB_bin0'] = {
        'hist': df.Filter(anaSetup.bMassRegions['SB']['cutString']).Histo1D(("h_KshortMass_SB_bin0", "", 30, 0.468, 0.528), "KshortMass"),
        'xTitle': "m_{#pi#pi#pi} [GeV]"}
    hists['h_KstarMass_bin0'] = {
        'hist': df.Histo1D(("h_KstarMass_bin0", "", 30, 0.742, 1.042), "KstarMass"),
        'xTitle': "m_{#pi^{+}#pi^{-}#pi^{#pm}} [GeV]"}
    hists['h_KstarMass_SR_bin0'] = {
        'hist': df.Filter(anaSetup.bMassRegions['SR']['cutString']).Histo1D(("h_KstarMass_SR_bin0", "", 30, 0.742, 1.042), "KstarMass"),
        'xTitle': "m_{#pi^{+}#pi^{-}#pi^{#pm}} [GeV]"}
    hists['h_KstarMass_SB_bin0'] = {
        'hist': df.Filter(anaSetup.bMassRegions['SB']['cutString']).Histo1D(("h_KstarMass_SB_bin0", "", 30, 0.742, 1.042), "KstarMass"),
        'xTitle': "m_{#pi^{+}#pi^{-}#pi^{#pm}} [GeV]"}
    hists['h_Bmass_LambdaSR_bin0'] = {
        'hist': df_LambdaSR.Histo1D(("h_Bmass_LambdaSR_bin0", "", 26, 4.76, 5.80), "Bmass"),
        'xTitle': "m_{B} [GeV]"}
    hists['h_Bmass_LambdaSR_bin1'] = {
        'hist': df_LambdaSR.Filter(anaSetup.q2bins['belowJpsi']['cutString']).Histo1D(("h_Bmass_LambdaSR_bin1", "", 26, 4.76, 5.80), "Bmass"),
        'xTitle': "m_{B} [GeV]"}
    hists['h_Bmass_LambdaSR_bin3'] = {
        'hist': df_LambdaSR.Filter(anaSetup.q2bins['betweenPeaks']['cutString']).Histo1D(("h_Bmass_LambdaSR_bin3", "", 26, 4.76, 5.80), "Bmass"),
        'xTitle': "m_{B} [GeV]"}
    hists['h_Bmass_LambdaSR_bin5'] = {
        'hist': df_LambdaSR.Filter(anaSetup.q2bins['abovePsi2s']['cutString']).Histo1D(("h_Bmass_LambdaSR_bin5", "", 26, 4.76, 5.80), "Bmass"),
        'xTitle': "m_{B} [GeV]"}

    h_Bmass_bin0 = df.Histo1D(("h_Bmass_bin0", "", 13, 4.76, 5.80), "Bmass")
    h_Bmass_VetoLambdaSR_bin0 = df_vetoLambdaSR.Histo1D(("h_Bmass_VetoLambdaSR_bin0", "", 13, 4.76, 5.80), "Bmass")
    
    canvas = Plotter.canvas
    canvas.cd()
    for hName, hData in hists.items():
        hData['hist'].SetMinimum(0)
        hData['hist'].SetMaximum(hData['hist'].GetMaximum()*1.8)
        hData['hist'].GetXaxis().SetTitle(hData.get('xTitle', ""))
        hData['hist'].GetYaxis().SetTitle(hData.get('yTitle', "Events"))
        hData['hist'].Draw("E")
        Plotter.latexDataMarks()
        canvas.Print(hName+".pdf")

    h_Bmass_bin0.GetXaxis().SetTitle("m_{B} [GeV]")
    h_Bmass_bin0.GetYaxis().SetTitle("Events")
    h_Bmass_bin0.SetMaximum(h_Bmass_bin0.GetMaximum()*1.8)
    h_Bmass_VetoLambdaSR_bin0.GetXaxis().SetTitle("m_{B} [GeV]")
    h_Bmass_VetoLambdaSR_bin0.GetYaxis().SetTitle("Events")
    h_Bmass_VetoLambdaSR_bin0.SetMarkerColor(2)
    h_Bmass_VetoLambdaSR_bin0.SetLineColor(2)
    h_Bmass_bin0.Draw("E")
    h_Bmass_VetoLambdaSR_bin0.Draw("E SAME")
    Plotter.latexDataMarks()
    canvas.Print(h_Bmass_VetoLambdaSR_bin0.GetName()+".pdf")
