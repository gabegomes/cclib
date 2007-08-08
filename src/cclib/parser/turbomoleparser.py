"""
cclib (http://cclib.sf.net) is (c) 2006, the cclib development team
and licensed under the LGPL (http://www.gnu.org/copyleft/lgpl.html).
"""

__revision__ = "$Revision: 635 $"

import re

# If numpy is not installed, try to import Numeric instead.
try:
    import numpy
except ImportError:
    import Numeric as numpy

import utils
import logfileparser


class AtomBasis:
    def __init__(self, atname, basis_name, inputfile):
        self.symmetries=[]
        self.coefficients=[]
        self.atname=atname
        self.basis_name=basis_name

        self.parse_basis(inputfile)

    def parse_basis(self, inputfile):
        i=0
        line=inputfile.next()

        while(line[0]!="*"):
            (nbasis_text, symm)=line.split()
            self.symmetries.append(symm)

            nbasis=int(nbasis_text)
            coeff_arr=numpy.zeros((nbasis, 2), float)

            for j in range(0, nbasis, 1):
                line=inputfile.next()
                (e1_text, e2_text)=line.split()
                coeff_arr[j][0]=float(e1_text)
                coeff_arr[j][1]=float(e2_text)

            self.coefficients.append(coeff_arr)
            line=inputfile.next()

class Turbomole(logfileparser.Logfile):
    """A Turbomole output file"""

    def __init__(self, *args):

        # Call the __init__ method of the superclass
        super(Turbomole, self).__init__(logname="Turbomole", *args)
        
    def __str__(self):
        """Return a string representation of the object."""
        return "Turbomole output file %s" % (self.filename)

    def __repr__(self):
        """Return a representation of the object."""
        return 'Turbomole("%s")' % (self.filename)

    def atlist(self, atstr):
        # turn atstr from atoms section into array

        fields=atstr.split(',')
        list=[]
        for f in fields:
            if(f.find('-')!=-1):
                rangefields=f.split('-')
                start=int(rangefields[0])
                end=int(rangefields[1])
                
                for j in range(start, end+1, 1):
                    list.append(j-1)
            else:
                list.append(int(f)-1)
        return(list)

    def normalisesym(self, label):
        """Normalise the symmetries used by Turbomole."""
        return ans

    def before_parsing(self):
        self.geoopt = False # Is this a GeoOpt? Needed for SCF targets/values.

    def split_molines(self, inline):
        line=inline.replace("D", "E")
        f1=line[0:20]
        f2=line[20:40]
        f3=line[40:60]
        f4=line[60:80]

        if(len(f4)>1):
            return( (float(f1), float(f2), float(f3), float(f4)) )
        if(len(f3)>1):
            return( (float(f1), float(f2), float(f3)) )
        if(len(f2)>1):
            return( (float(f1), float(f2)) )
        if(len(f1)>1):
            return([float(f1)])
        return
    
    def extract(self, inputfile, line):
        """Extract information from the file object inputfile."""

        if line[3:11]=="nbf(AO)=":
            nmo=int(line[11:])
            self.nbasis=nmo
            self.nmo=nmo
        if line[3:9]=="nshell":
            temp=line.split('=')
            homos=int(temp[1])

        if line == "$basis\n":
            self.basis_lib=[]
            line = inputfile.next()
            line = inputfile.next()

            while line[0] != '*' and line[0] != '$':
                temp=line.split()
                line = inputfile.next()
                while line[0]=="#":
                    line = inputfile.next()
                self.basis_lib.append(AtomBasis(temp[0], temp[1], inputfile))
                line = inputfile.next()

        if line == "$coord\n":
            self.atomcoords = []
            self.atomnos = []
            atomcoords = []
            atomnos = []

            line = inputfile.next()

            while line[0] != "$":
                temp = line.split()
                atsym=temp[3].capitalize()
                atomnos.append(self.table.number[atsym])
                atomcoords.append([utils.convertor(float(x), "bohr", "Angstrom")
                                   for x in temp[0:3]])
                line = inputfile.next()
            self.atomcoords.append(atomcoords)
            self.atomnos = numpy.array(atomnos, "i")

        if line == "$atoms\n":
            line = inputfile.next()
            self.atomlist=[]
            while line[0]!="$":
                temp=line.split()
                at=temp[0]
                atnosstr=temp[1]
                while temp[1][len(temp[1])-1] == ',':
                    line = inputfile.next()
                    temp=line.split()
                    atnosstr=atnosstr+temp[0]
                atlist=self.atlist(atnosstr)

                line = inputfile.next()

                temp=line.split()
                basisname=temp[2]

                line = inputfile.next()
                while(line.find('jbas')!=-1 or line.find('ecp')!=-1 or
                      line.find('jkbas')!=-1):
                    line = inputfile.next()

                self.atomlist.append( (at, basisname, atlist))

        if line[3:10]=="natoms=":
            self.natom=int(line[10:])
            basistable=[]

            self.atomlist
            for i in range(0, self.natom, 1):
                for j in range(0, len(self.atomlist), 1):
                    for k in range(0, len(self.atomlist[j][2]), 1):
                        if(self.atomlist[j][2][k]==i):
                            basistable.append((self.atomlist[j][0],
                                                   self.atomlist[j][1]))
            self.aonames=[]
            counter=1
            for a, b in basistable:
                for i in range(0, len(self.basis_lib), 1):
                    if self.basis_lib[i].atname==a and self.basis_lib[i].basis_name==b:
                        pa=a.capitalize()

                        basis=self.basis_lib[i]
                        for j in range(0, len(basis.symmetries), 1):
                            if basis.symmetries[j]=='s':
                                self.aonames.append("%s%d_%d%s" % \
                                              (pa, counter, j+1, "S"))
                            elif basis.symmetries[j]=='p':
                                self.aonames.append("%s%d_%d%s" % \
                                              (pa, counter, j-1, "PX"))
                                self.aonames.append("%s%d_%d%s" % \
                                              (pa, counter, j-1, "PY"))
                                self.aonames.append("%s%d_%d%s" % \
                                              (pa, counter, j-1, "PZ"))
                            elif basis.symmetries[j]=='d':
                                self.aonames.append("%s%d_%d%s" % \
                                                    (pa, counter, j-2, "D 0"))
                                self.aonames.append("%s%d_%d%s" % \
                                                   (pa, counter, j-2, "D+1"))
                                self.aonames.append("%s%d_%d%s" % \
                                                   (pa, counter, j-2, "D-1"))
                                self.aonames.append("%s%d_%d%s" % \
                                                    (pa, counter, j-2, "D+2"))
                                self.aonames.append("%s%d_%d%s" % \
                                                    (pa, counter, j-2, "D-2"))
                        break
                counter=counter+1
                
        if line=="$closed shells\n":
            line = inputfile.next()
            temp = line.split()
            occs = int(temp[1][2:])
            self.homos = numpy.array([occs-1], "i")
        if line[12:24]=="OVERLAP(CAO)":
            line = inputfile.next()
            line = inputfile.next()
            overlaparray=[]
            self.aooverlaps=numpy.zeros( (self.nbasis, self.nbasis), "d")
            while line != "       ----------------------\n":
                temp=line.split()
                overlaparray.extend(map(float, temp))
                line = inputfile.next()
            counter=0

            for i in range(0, self.nbasis, 1):
                for j in range(0, i+1, 1):
                    self.aooverlaps[i][j]=overlaparray[counter]
                    self.aooverlaps[j][i]=overlaparray[counter]
                    counter=counter+1

        if line[0:6] == "$scfmo" and line.find("scfconv")>-1:
            self.moenergies=[]
            self.mocoeffs=[]
            moarray=[]
            title = inputfile.next()
            while(title[0] == "#"):
                title = inputfile.next()
            mocoeffs = numpy.zeros((self.nbasis, self.nbasis), "d")

            while(title[0] != '$'):
                temp=title.split()

                orb_symm=temp[1]
                orb_en=float(temp[2][20:].replace("D", "E"))

                self.moenergies.append(orb_en)
                single_mo = []
                
                while(len(single_mo)<self.nbasis):
                    title = inputfile.next()
                    lines_coeffs=self.split_molines(title)
                    single_mo.extend(lines_coeffs)
                    
                moarray.append(single_mo)
                title = inputfile.next()

            for i in range(0, len(moarray), 1):
                for j in range(0, self.nbasis, 1):
                    mocoeffs[i][j]=moarray[i][j]

            self.mocoeffs.append(mocoeffs)
