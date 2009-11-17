"""Clusters are generalised constraints on sets of points in R^n. Cluster
types are Rigids, Hedgehogs and Balloons. """

from sets import Set, ImmutableSet
from multimethod import MultiVariable

class Distance:
    """A Distance represents a known distance"""


    def __init__(self, a, b):
        """Create a new Distance
        
           keyword args:
            a - point variable
            b - point variable
        """
        self.vars = (a,b)
    
    def __str__(self):
        return "dist("\
            +str(self.vars[0])+","\
            +str(self.vars[1])+")"

    def __hash__(self):
        return hash(ImmutableSet(self.vars))

    def __eq__(self, other):
        if isinstance(other, Distance):
            return ImmutableSet(self.vars) == ImmutableSet(other.vars)
        else:
            return False


class Angle:
    """A Angle represents a known angle"""

    def __init__(self, a, b, c):
        """Create a new Angle
        
           keyword args:
            a - point variable
            b - point variable
            c - point variable
        """
        self.vars = (a,b,c)

    def __eq__(self, other):
        if isinstance(other, Angle):
            return self.vars[2] == other.vars[2] and ImmutableSet(self.vars) == ImmutableSet(other.vars)
        else:
            return False


    def __hash__(self):
        return hash(ImmutableSet(self.vars))

    def __str__(self):
        return "ang("\
            +str(self.vars[0])+","\
            +str(self.vars[1])+","\
            +str(self.vars[2])+")"


class Cluster(MultiVariable):
    """A set of points, satisfying some constaint"""
    
    staticcounter = 0

    def __init__(self):
        Cluster.staticcounter += 1
        self.creationtime = Cluster.staticcounter

    def intersection(self, other):
        shared = Set(self.vars).intersection(other.vars)
        # note, a one point cluster is never returned 
        #because it is not a constraint
        if len(shared) < 2:   
            return None
        elif isinstance(self, Rigid): 
            if isinstance(other, Rigid):
                if len(shared) >= 2:
                    return Rigid(shared)
                else:
                    return None
            elif isinstance(other, Balloon):
                if len(shared) >= 3:
                    return Balloon(shared)
                else:
                    return None
            elif isinstance(other, Hedgehog):
                xvars = Set(shared) - Set([other.cvar])
                if other.cvar in self.vars and len(xvars) >= 2:
                    return Hedgehog(other.cvar,xvars)
                else:
                    return None
        elif isinstance(self, Balloon):
            if isinstance(other, Rigid) or isinstance(other, Balloon):
                if len(shared) >= 3:
                    return Balloon(shared)
                else:
                    return None
            elif isinstance(other, Hedgehog):
                xvars = Set(shared) - Set([other.cvar])
                if other.cvar in self.vars and len(xvars) >= 2:
                    return Hedgehog(other.cvar,xvars)
                else:
                    return None
        elif isinstance(self, Hedgehog):
            if isinstance(other, Rigid) or isinstance(other, Balloon):
                xvars = Set(shared) - Set([self.cvar])
                if self.cvar in other.vars and len(xvars) >= 2:
                    return Hedgehog(self.cvar,xvars)
                else:
                    return None
            elif isinstance(other, Hedgehog):
                xvars = Set(self.xvars).intersection(other.xvars)
                if self.cvar == other.cvar and len(xvars) >= 2:
                    return Hedgehog(self.cvar,xvars)
                else:
                    return None
        # if all fails
        raise Exception("intersection of unknown Cluster types")

 
class Rigid(Cluster):
    """A Rigid (or RigidCluster) represent a cluster of points variables 
       that forms a rigid body."""

    def __init__(self, vars):
        """Create a new cluster
        
           keyword args:
            vars - list of variables 
        """
        Cluster.__init__(self)
        self.vars = ImmutableSet(vars)
        self.overconstrained = False

    def __str__(self):
        s = "rigid#"+str(id(self))+"("+str(map(str, self.vars))+")"
        if self.overconstrained:
            s = "!" + s
        return s

    def copy(self):
        new = Rigid(self.vars)
        new.overconstrained = self.overconstrained
        return new

           

class Hedgehog(Cluster):
    """An Hedgehog (or AngleCluster) represents a set of points (M,X1...XN) 
       where all angles a(Xi,M,Xj) are known. 
    """
    def __init__(self, cvar, xvars):
        """Create a new hedgehog
        
           keyword args:
            cvar - center variable 
            xvars - list of variables
        """ 
        Cluster.__init__(self)
        self.cvar = cvar
        if len(xvars) < 2:
            raise StandardError, "hedgehog must have at least three variables"
        self.xvars = ImmutableSet(xvars)
        self.vars = self.xvars.union([self.cvar])
        self.overconstrained = False

    def __str__(self):
        s = "hedgehog#"+str(id(self))+"("+str(self.cvar)+","+str(map(str, self.xvars))+")"
        if self.overconstrained:
            s = "!" + s
        return s

    def copy(self):
        new = Hedgehog(self.cvar, self.xvars)
        new.overconstrained = self.overconstrained
        return new


class Balloon(Cluster):
    """A Balloon (or ScalableCluster) is set of points that is 
       invariant to rotation, translation and scaling.
    """
    def __init__(self, variables):
        """Create a new balloon
        
           keyword args:
            vars - collection of PointVar's
        """
        Cluster.__init__(self)
        if len(variables) < 3:
            raise StandardError, "balloon must have at least three variables"
        self.vars = ImmutableSet(variables)
        self.overconstrained = False

    def __str__(self):
        s = "balloon#"+str(id(self))+"("+str(map(str, self.vars))+")"
        if self.overconstrained:
            s = "!" + s
        return s

    def copy(self):
        new = Balloon(self.vars)
        new.overconstrained = self.overconstrained
        return new

# ----- function to determine overconstraints -----

def over_constraints(c1, c2):
    """returns the over-constraints (duplicate distances and angles) for
       a pair of clusters (rigid, angle or scalable)."""
    return over_distances(c1,c2).union(over_angles(c1,c2))    
    
def over_angles(c1, c2):
    if isinstance(c1,Rigid) and isinstance(c2,Rigid):
        return over_angles_bb(c1,c2)
    if isinstance(c1,Rigid) and isinstance(c2,Hedgehog):
        return over_angles_ch(c1,c2)
    elif isinstance(c1,Hedgehog) and isinstance(c2,Rigid):
        return over_angles_ch(c2,c1)
    elif isinstance(c1,Hedgehog) and isinstance(c2,Hedgehog):
        return over_angles_hh(c1,c2)
    elif isinstance(c1,Rigid) and isinstance(c2,Balloon):
        return over_angles_cb(c1,c2)
    elif isinstance(c1,Balloon) and isinstance(c2,Rigid):
        return over_angles_cb(c1,c2)
    elif isinstance(c1,Balloon) and isinstance(c2,Balloon):
        return over_angles_bb(c1,c2)
    elif isinstance(c1,Balloon) and isinstance(c2,Hedgehog):
        return over_angles_bh(c1,c2)
    elif isinstance(c1,Hedgehog) and isinstance(c2,Balloon):
        return over_angles_bh(c2,c1)
    else:
        raise StandardError, "unexpected case"
    
def over_distances(c1, c2):
        """determine set of distances in c1 and c2"""
        if not (isinstance(c1, Rigid) and isinstance(c2, Rigid)):
            return Set()
        else:
            shared = list(Set(c1.vars).intersection(c2.vars))
            overdists = Set()
            for i in range(len(shared)):
                for j in range(i):
                    v1 = shared[i]
                    v2 = shared[j]
                    overdists.add(Distance(v1,v2))
            return overdists

def over_angles_hh(hog1, hog2):
        # determine duplicate angles
        shared = list(Set(hog1.xvars).intersection(hog2.xvars))
        if not hog1.cvar == hog2.cvar:
            return Set()
        overangles = Set()
        for i in range(len(shared)):
            for j in range(i):
                v1 = shared[i]
                v2 = shared[j]
                overangles.add(Angle(v1,hog1.cvar,v2))
        return overangles

def over_angles_bb(b1, b2):
        # determine duplicate angles
        shared = list(Set(b1.vars).intersection(b2.vars))
        overangles = Set()
        for i in range(len(shared)):
            for j in range(i+1, len(shared)):
                for k in range(j+1, len(shared)):
                    v1 = shared[i]
                    v2 = shared[j]
                    v3 = shared[k]
                    overangles.add(Angle(v1,v2,v3))
                    overangles.add(Angle(v2,v3,v1))
                    overangles.add(Angle(v3,v1,v2))
        return overangles

def over_angles_cb(cluster, balloon):
        # determine duplicate angles
        # note: identical to over_angles_bb and (non-existent) over_angles_cc
        shared = list(Set(cluster.vars).intersection(balloon.vars))
        overangles = Set()
        for i in range(len(shared)):
            for j in range(i+1, len(shared)):
                for k in range(j+1, len(shared)):
                    v1 = shared[i]
                    v2 = shared[j]
                    v3 = shared[k]
                    overangles.add(Angle(v1,v2,v3))
                    overangles.add(Angle(v2,v3,v1))
                    overangles.add(Angle(v3,v1,v2))
        return overangles

def over_angles_bh(balloon, hog):
        # determine duplicate angles
        shared = list(Set(balloon.vars).intersection(hog.xvars))
        if hog.cvar not in balloon.vars:
            return Set()
        overangles = Set()
        for i in range(len(shared)):
            for j in range(i+1,len(shared)):
                v1 = shared[i]
                v2 = shared[j]
                overangles.add(Angle(v1,hog.cvar,v2))
        return overangles

def over_angles_ch(cluster, hog):
        # determine duplicate angles
        shared = list(Set(cluster.vars).intersection(hog.xvars))
        if hog.cvar not in cluster.vars:
            return Set()
        overangles = Set()
        for i in range(len(shared)):
            for j in range(i+1,len(shared)):
                v1 = shared[i]
                v2 = shared[j]
                overangles.add(Angle(v1,hog.cvar,v2))
        return overangles

def binomial(n,k):
    p = 1
    for j in range(0,k):
        p = p*(n - j)/(j + 1)
    return p

def num_constraints(cluster):
    return num_distances(cluster)+num_angles(cluster)

def num_distances(cluster):
    if isinstance(cluster, Rigid):
        n = len(cluster.vars)
        return binomial(n,2)
    else:
        return 0

def num_angles(cluster):
    if isinstance(cluster, Balloon) or isinstance(cluster, Rigid):
        n = len(cluster.vars)
        return binomial(n,3) * 3
    elif isinstance(cluster, Hedgehog):
        n = len(cluster.xvars)
        return binomial(n,2)
    else:
        return 0

def test():
    r = Rigid([1,3,4,5])
    b = Balloon([1,2,3,4])
    h = Hedgehog(1,[2,3,5])
    print "self intersections"
    print r.intersection(r)
    print b.intersection(b)
    print h.intersection(h)
    print "cross intersections (2x)"
    print r.intersection(b)
    print b.intersection(r)
    print r.intersection(h)
    print h.intersection(r)
    print b.intersection(h)
    print h.intersection(b)
    print "double intersection (3x)"
    print r.intersection(b).intersection(h)
    print r.intersection(h).intersection(b)
    print b.intersection(h).intersection(r)


if __name__ == "__main__": test()
