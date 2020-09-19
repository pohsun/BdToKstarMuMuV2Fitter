// vim: sw=4 ts=4 fdm=syntax fdl=0 fdn=2 et:
#include <cstdio>
#include <stdexcept>

#include "Constants.h"
#include "ROOT/RVec.hxx"
#include "TLorentzVector.h"

ROOT::VecOps::RVec<int> DefineBit_HasGoodDimuon(
    const ROOT::VecOps::RVec<bool> mumisgoodmuon,
    const ROOT::VecOps::RVec<bool> mupisgoodmuon,
    const ROOT::VecOps::RVec<int> mumntrklayers,
    const ROOT::VecOps::RVec<int> mupntrklayers,
    const ROOT::VecOps::RVec<int> mumnpixlayers,
    const ROOT::VecOps::RVec<int> mupnpixlayers,
    const ROOT::VecOps::RVec<double> mumnormchi2,
    const ROOT::VecOps::RVec<double> mupnormchi2,
    const ROOT::VecOps::RVec<double> mumdxyvtx,
    const ROOT::VecOps::RVec<double> mupdxyvtx,
    const ROOT::VecOps::RVec<double> mumdzvtx,
    const ROOT::VecOps::RVec<double> mupdzvtx){

    auto checker_muntrklayers = [](const int &m) -> bool {return m>5;};
    auto Define_mumntrklayers = ROOT::VecOps::Map(mumntrklayers, checker_muntrklayers);
    auto Define_mupntrklayers = ROOT::VecOps::Map(mupntrklayers, checker_muntrklayers);

    auto checker_munpixlayers = [](const int &m) -> bool {return m>0;};
    auto Define_mumnpixlayers = ROOT::VecOps::Map(mumnpixlayers, checker_munpixlayers);
    auto Define_mupnpixlayers = ROOT::VecOps::Map(mupnpixlayers, checker_munpixlayers);
//
    auto checker_munormchi2 = [](const double &m) -> bool {return m<1.8;};
    auto Define_mumnormchi2 = ROOT::VecOps::Map(mumnormchi2, checker_munormchi2);
    auto Define_mupnormchi2 = ROOT::VecOps::Map(mupnormchi2, checker_munormchi2);
//
    auto checker_mudxyvtx = [](const double &m) -> bool {return fabs(m)<0.3;};
    auto Define_mumdxyvtx = ROOT::VecOps::Map(mumdxyvtx, checker_mudxyvtx);
    auto Define_mupdxyvtx = ROOT::VecOps::Map(mupdxyvtx, checker_mudxyvtx);
//
    auto checker_mudzvtx = [](const double &m) -> bool {return fabs(m)<20.;};
    auto Define_mumdzvtx = ROOT::VecOps::Map(mumdzvtx, checker_mudzvtx);
    auto Define_mupdzvtx = ROOT::VecOps::Map(mupdzvtx, checker_mudzvtx);

    ROOT::VecOps::RVec<int> hasgooddimuon(mumisgoodmuon.size(), 1);
    for(size_t i=0; i < hasgooddimuon.size(); i++){
        if (!mumisgoodmuon.at(i)
            || !mupisgoodmuon.at(i)
            || !Define_mumntrklayers.at(i)
            || !Define_mupntrklayers.at(i)
            || !Define_mumnpixlayers.at(i)
            || !Define_mupnpixlayers.at(i)
            || !Define_mumnormchi2.at(i)
            || !Define_mupnormchi2.at(i)
            || !Define_mumdxyvtx.at(i)
            || !Define_mupdxyvtx.at(i)
            || !Define_mumdzvtx.at(i)
            || !Define_mupdzvtx.at(i)
        ){
            hasgooddimuon.at(i) = 0;
        }
    }
    return hasgooddimuon;
}

ROOT::VecOps::RVec<int> DefineBit_trkpt(const ROOT::VecOps::RVec<double> &trkpt){
    auto checker = [](const double &p) -> int {return p>0.4 ? 1 : 0;};
    return ROOT::VecOps::Map(trkpt, checker);
}

ROOT::VecOps::RVec<int> DefineBit_trkdcabssig(const ROOT::VecOps::RVec<double> &trkdcabs, const ROOT::VecOps::RVec<double> &trkdcabserr){
    ROOT::VecOps::RVec<int> output(trkdcabs.size(), 0);

    auto checker = [](const double &p, const double &perr)-> int {return fabs(p/perr)>0.4 ? 1 : 0;};
    for(size_t i=0; i < trkdcabs.size(); ++i){
        output.at(i) = checker(trkdcabs.at(i), trkdcabserr.at(i));
    }
    return output;
}

ROOT::VecOps::RVec<int> DefineBit_kspt(const ROOT::VecOps::RVec<double> &kspx, const ROOT::VecOps::RVec<double> &kspy){
    ROOT::VecOps::RVec<int> output(kspx.size(), 0);

    auto checker = [](const double &px, const double &py) -> int {return sqrt(pow(px, 2) + pow(py, 2))>1. ? 1 : 0;};
    for(size_t i=0; i < kspx.size(); ++i){
        output.at(i) = checker(kspx.at(i), kspy.at(i));
    }
    return output;
}

ROOT::VecOps::RVec<int> DefineBit_bvtxcl(const ROOT::VecOps::RVec<double> &bvtxcl){
    auto checker = [](const double &p) -> int {return p>0.1 ? 1 : 0;};
    return ROOT::VecOps::Map(bvtxcl, checker);
}

ROOT::VecOps::RVec<int> DefineBit_blsbssig(const ROOT::VecOps::RVec<double> &blsbs, const ROOT::VecOps::RVec<double> &blsbserr){
    ROOT::VecOps::RVec<int> output(blsbs.size(), 0);

    auto checker = [](const double &p, const double &perr) -> int {return fabs(p/perr)>12 ? 1 : 0;};
    for(size_t i=0; i < blsbs.size(); ++i){
        output.at(i) = checker(blsbs.at(i), blsbserr.at(i));
    }
    return output;
}

ROOT::VecOps::RVec<int> DefineBit_bcosalphabs2d(const ROOT::VecOps::RVec<double> &bcosalphabs2d){
    auto checker = [](const double &p) -> int {return p>0.9994 ? 1 : 0;};
    return ROOT::VecOps::Map(bcosalphabs2d, checker);
}

ROOT::VecOps::RVec<int> DefineBit_kstarmass(const ROOT::VecOps::RVec<double> &kstarmass){
    auto checker = [](const double &p) -> int {return (p>0.742 && p<1.042) ? 1 : 0;};
    return ROOT::VecOps::Map(kstarmass, checker);
}

ROOT::VecOps::RVec<int> DefineBit_bmass(const ROOT::VecOps::RVec<double> &bmass){
    auto checker = [](const double &p) -> int {return (p>4.5 && p<6.0) ? 1 : 0;};
    return ROOT::VecOps::Map(bmass, checker);
}

ROOT::VecOps::RVec<int> DefineBit_lambdaVeto(
        const ROOT::VecOps::RVec<double> &pippx,
        const ROOT::VecOps::RVec<double> &pippy,
        const ROOT::VecOps::RVec<double> &pippz,
        const ROOT::VecOps::RVec<double> &pimpx,
        const ROOT::VecOps::RVec<double> &pimpy,
        const ROOT::VecOps::RVec<double> &pimpz){
    ROOT::VecOps::RVec<int> output(pippx.size(), -BIGNUMBER);
    TLorentzVector pi_4vec, p_4vec;
    auto calc_p = [](const double &px, const double &py, const double &pz) -> double {return sqrt(pow(px,2)+pow(py,2)+pow(pz,2));};
    auto isLambdaVeto = [](double m) -> int {return (m<1.11 || m >1.125);};
    for(unsigned int tkIndex =0; tkIndex < pippx.size(); tkIndex++){
        if (calc_p(pippx.at(tkIndex), pippy.at(tkIndex), pippz.at(tkIndex)) > calc_p(pimpx.at(tkIndex), pimpy.at(tkIndex), pimpz.at(tkIndex))){
            p_4vec.SetXYZM(pippx.at(tkIndex), pippy.at(tkIndex), pippz.at(tkIndex), PROTON_MASS);
            pi_4vec.SetXYZM(pimpx.at(tkIndex), pimpy.at(tkIndex), pimpz.at(tkIndex), PION_MASS);
        }else{
            p_4vec.SetXYZM(pimpx.at(tkIndex), pimpy.at(tkIndex), pimpz.at(tkIndex), PROTON_MASS);
            pi_4vec.SetXYZM(pippx.at(tkIndex), pippy.at(tkIndex), pippz.at(tkIndex), PION_MASS);
        }
        output.at(tkIndex) = isLambdaVeto((pi_4vec+p_4vec).M());
    }
    return output;
}

ROOT::VecOps::RVec<double> Define_cosThetaL(
        const ROOT::VecOps::RVec<double> &bpx,
        const ROOT::VecOps::RVec<double> &bpy,
        const ROOT::VecOps::RVec<double> &bpz,
        const ROOT::VecOps::RVec<double> &bmass,
        const ROOT::VecOps::RVec<int> &bchg,
        const ROOT::VecOps::RVec<double> &mumpx,
        const ROOT::VecOps::RVec<double> &mumpy,
        const ROOT::VecOps::RVec<double> &mumpz,
        const ROOT::VecOps::RVec<double> &muppx,
        const ROOT::VecOps::RVec<double> &muppy,
        const ROOT::VecOps::RVec<double> &muppz){
    ROOT::VecOps::RVec<double> output(bmass.size(), -BIGNUMBER);
    TLorentzVector B_4vec, Mup_4vec, Mum_4vec, buff1, buff2, buff3;

	for(unsigned int BIndex =0; BIndex < bmass.size(); BIndex++){
		B_4vec.SetXYZM(bpx.at(BIndex),bpy.at(BIndex),bpz.at(BIndex),bmass.at(BIndex));
		Mup_4vec.SetXYZM(muppx.at(BIndex),muppy.at(BIndex),muppz.at(BIndex),0.10565837);
		Mum_4vec.SetXYZM(mumpx.at(BIndex),mumpy.at(BIndex),mumpz.at(BIndex),0.10565837);

		buff1 = B_4vec;
		buff2 = Mup_4vec + Mum_4vec;
		buff1.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());

		buff3 = bchg.at(BIndex)>0 ? Mum_4vec : Mup_4vec;//Take mu- to avoid extra minus sign.
		buff3.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());

		output.at(BIndex) = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();
	}
    return output;
}

ROOT::VecOps::RVec<double> Define_cosThetaK(
        const ROOT::VecOps::RVec<double> &bpx,
        const ROOT::VecOps::RVec<double> &bpy,
        const ROOT::VecOps::RVec<double> &bpz,
        const ROOT::VecOps::RVec<double> &bmass,
        const ROOT::VecOps::RVec<double> &kstarmass,
        const ROOT::VecOps::RVec<double> &kspx,
        const ROOT::VecOps::RVec<double> &kspy,
        const ROOT::VecOps::RVec<double> &kspz,
        const ROOT::VecOps::RVec<double> &trkpx,
        const ROOT::VecOps::RVec<double> &trkpy,
        const ROOT::VecOps::RVec<double> &trkpz){
    ROOT::VecOps::RVec<double> output(bmass.size(), -BIGNUMBER);
    TLorentzVector B_4vec, Kst_4vec, Tk_4vec, buff1, buff2, buff3;

	for(unsigned int BIndex =0; BIndex < bmass.size(); BIndex++){
		B_4vec.SetXYZM(bpx.at(BIndex),bpy.at(BIndex),bpz.at(BIndex),bmass.at(BIndex));
        Kst_4vec.SetXYZM(kspx.at(BIndex)+trkpx.at(BIndex),kspy.at(BIndex)+trkpy.at(BIndex),kspz.at(BIndex)+trkpz.at(BIndex),kstarmass.at(BIndex));
		Tk_4vec.SetXYZM(trkpx.at(BIndex),trkpy.at(BIndex),trkpz.at(BIndex),PION_MASS);

		buff1 = B_4vec;
		buff2 = Kst_4vec;
		buff1.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());

		buff3 = Tk_4vec;//Take pion to avoid extra minus.
		buff3.Boost(-buff2.X()/buff2.T(),-buff2.Y()/buff2.T(),-buff2.Z()/buff2.T());

		output.at(BIndex) = buff1.Vect().Dot(buff3.Vect())/buff1.Vect().Mag()/buff3.Vect().Mag();
	}
    return output;
}

bool Filter_IsNonEmptyBit(const ROOT::VecOps::RVec<int> &bits){
    for(auto &bit: bits){
        if (bit > 0){
            return true;
        }
    }
    return false;
}

template<class TTar, class TRef> 
TTar Define_GetValAtArgMax(const ROOT::VecOps::RVec<TTar> &targetCol, const ROOT::VecOps::RVec<TRef> &refCol){
    return targetCol.at(std::distance(refCol.begin(), std::max_element(refCol.begin(), refCol.end())));
}

template<class TRef> 
int Define_GetArgMax(const ROOT::VecOps::RVec<TRef> &refCol, const ROOT::VecOps::RVec<int> &bitSwitch){
    int argmax = -1;
    for(int ibit = 0; ibit < bitSwitch.size(); ibit++){
        if ( bitSwitch.at(ibit)==1 && ( argmax==-1 || (refCol.at(ibit)>refCol.at(argmax)) )){
            argmax = ibit;
        }
    }
    if (argmax > -1){
        return argmax;
    }else{
        throw std::runtime_error("No available ArgMax in bits column, please drop event with emtpy bits with Filter_IsEmptyBit.");
    }
}

template<class TTar, class TRef> 
TTar Define_GetValAtArgMax(const ROOT::VecOps::RVec<TTar> &targetCol, const ROOT::VecOps::RVec<TRef> &refCol, const ROOT::VecOps::RVec<int> &bitSwitch){
    int argmax = Define_GetArgMax(refCol, bitSwitch);
    return targetCol.at(argmax);
}

template<class TTar>
TTar Define_GetSum(const ROOT::VecOps::RVec<TTar> &targetCol, const ROOT::VecOps::RVec<int> &bitSwitch){
    TTar sum = 0;
    for(int ibit = 0; ibit < targetCol.size(); ibit++){
        if (bitSwitch.at(ibit) > 0){
            sum += targetCol.at(ibit);
        }
    }
    return sum;
}

template<class TTar>
TTar Define_GetSum(const ROOT::VecOps::RVec<TTar> &targetCol){
    TTar sum = 0;
    for(auto &ibin: targetCol){
        sum += ibin;
    }
    return sum;
}

template<class TTar>
int Define_CountNonzero(const ROOT::VecOps::RVec<TTar> &targetCol){
    int sum = 0;
    for(auto &ibin: targetCol){
        if (ibin != 0){
            sum += 1;
        }
    }
    return sum;
}
