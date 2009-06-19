from django.db import models
import unittest

class Node(models.Model):
    """ base class to define the standard RDF/N3 node attributes """
    name = models.SlugField()
    label = models.CharField(max_length=256)
    comment = models.TextField(blank=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.label

class Predicate(Node):
    """
    >>> human = Predicate.objects.create(name='human',label='is Human',comment='')
    >>> human.label
    'is Human'
    >>> mortal = Predicate.objects.create(name='mortal',label='is Mortal')
    >>> mortal.label
    'is Mortal'
    """
    
    def id_exp(self):
        exp = Expression.objects.create(operator='ID')
        t = ExpressionPredicate.objects.create(expression=exp,predicate=self)
        return exp

    def expressions(self):
        return [ep.expression for ep in self.expressionpredicate_set.all()]

class Expression(models.Model):
    """
    >>> h_exp = Expression.objects.create(operator='AND')
    >>> m_exp = Expression.objects.create(operator='AND')
    """
    operator = models.CharField(max_length=5,
                                default="ID",
                                choices=(
        ('ID','ID'), # an identity operator, for single term expressions
        ('AND','AND'),
        ('OR','OR'),
        ('NOT','NOT'),
        ),
                                )

    def predicate(self):
        assert self.operator == "ID" or self.operator == "NOT"
        return self.expressionpredicate_set.all()[0].predicate

    def children(self):
        assert self.operator != "ID"
        return [ec.child for ec in ExpressionChild.objects.filter(parent=self)]

    def __unicode__(self):
        if self.operator == "ID":
            return "(" + str(self.predicate()) + ")"
        else:
            return "(" + self.operator + " " + \
                   " ".join([str(c) for c in self.children()]) \
                   + ")"


    def parents(self):
        return [ec.parent for ec in ExpressionChild.objects.filter(child=self)]

    def all_parents(self):
        """ recursively up the tree """
        ps = self.parents()
        allps = []
        allps += ps
        for p in ps:
            grandparents = p.all_parents()
            if grandparents:
                allps += grandparents
        return allps

    def antecedent_rules(self):
        """ all the rules that have this expression or a parent of this expression
        as the antecedent """
        direct = list(Rule.objects.filter(antecedent=self))
        # no attempt to remove duplicates at first
        for p in self.all_parents():
            direct += p.antecedent_rules()
        return direct

    def evaluate(self,truth_values=None):
        """ return True, False, or None (indeterminate) from attempting
        to evaluate this expression given the truth_values specified """
        if truth_values is None:
            truth_values = dict()
        if self.operator == "ID":
            # should just be a single term
            p = self.predicate()
            if p.id in truth_values:
                return truth_values[p.id]
            else:
                return None
        else:

            subterms = [e.evaluate(truth_values) for e in self.children()]
            if self.operator == "AND":
                # we can short-circuit on False
                if False in subterms:
                    return False
                if None in subterms:
                    # a subterm couldn't be evaluated
                    return None
                else:
                    return reduce(lambda a,b: a and b, subterms)
            elif self.operator == "OR":
                # we can short-circuit on True
                if True in subterms:
                    return True
                if None in subterms:
                    # it has to be either [None] or None + some Falses
                    return None
                # if we get here, it's all Falses (or an empty list,
                # which *shouldn't* be possible)
                assert len(subterms) > 0
                return False
            elif self.operator == "NOT":
                c = self.children()[0].evaluate(truth_values)
                if c is None:
                    return c
                else:
                    return not c
            else:
                # unknown operator
                return None

    def antecedent_rules(self):
        return Rule.objects.filter(antecedent=self)

    def all_antecedent_rules(self):
        direct = list(self.antecedent_rules())
        for p in self.all_parents():
            direct += p.all_antecedent_rules()
        return direct

class ExpressionPredicate(models.Model):
    expression = models.ForeignKey(Expression) 
    predicate = models.ForeignKey(Predicate)

    def __unicode__(self):
        return str(self.predicate)

class ExpressionChild(models.Model):
    parent = models.ForeignKey(Expression,related_name='parent')
    child = models.ForeignKey(Expression,related_name='child')


class Rule(Node):
    antecedent = models.ForeignKey(Expression,related_name='antecedent')
    consequent = models.ForeignKey(Expression,related_name='consequent')

    def __unicode__(self):
        return str(self.antecedent) + " => " + str(self.consequent)

    def evaluate(self,truth_values):
        av = self.antecedent.evaluate(truth_values)
        results = dict()
        if av is None:
            # didn't have enough info to evaluate
            print "not enough info"
            return results
        if av:
            if self.consequent.operator == "ID":
                results[self.consequent.predicate().id] = True
            else:
                # can't handle this yet
                pass
        else:
            # antecedent was false, so we can't get anything
            pass
        return results

def entail(truth_values=None):
    if truth_values is None:
        truth_values = dict()

    combined = truth_values.copy()

    found_new = False
    for pid in truth_values.keys():
        p = Predicate.objects.get(id=pid)
        for e in p.expressions():
            for r in e.all_antecedent_rules():
                results = r.evaluate(truth_values)
                for k in results.keys():
                    if k not in combined:
                        found_new = True
                combined.update(results)

    if found_new:
        print "found new so running again"
        new_results = entail(combined)
        combined.update(new_results)
    else:
        print "bottomed out"

    return combined
    


class BasicTest(unittest.TestCase):
    def testBasic(self):
        human = Predicate.objects.create(name='human',label='is Human',comment='')
        mortal = Predicate.objects.create(name='mortal',label='is Mortal')
        god = Predicate.objects.create(name="god",label="is a God")
        immortal = Predicate.objects.create(name='immortal',label='is Immortal')
        
        h_exp = human.id_exp()
        m_exp = mortal.id_exp()
        g_exp = god.id_exp()

        i_exp = Expression.objects.create(operator='NOT')
        i_term = ExpressionChild.objects.create(parent=i_exp,
                                                child=m_exp)
        
        r = Rule.objects.create(name='example',label='example rule',
                                antecedent=h_exp,consequent=m_exp)
        r2 = Rule.objects.create(name='immortal',label='immortality rule',
                                 antecedent=g_exp,consequent=i_exp)
        
        
        self.assertEquals(str(r),"(is Human) => (is Mortal)")

        self.assertEquals(str(r2),"(is a God) => (NOT (is Mortal))")
        print "trying r2"
        results = entail({human.id : True})
        self.assertEquals(results[mortal.id],True)

        a = Predicate.objects.create(name="a",label="a")
        b = Predicate.objects.create(name="b",label="b")
        c = Predicate.objects.create(name="c",label="c")
        
        a_exp = a.id_exp()
        b_exp = b.id_exp()
        c_exp = c.id_exp()

        ant_exp = Expression.objects.create(operator='AND')
        a_term = ExpressionChild.objects.create(parent=ant_exp,child=a_exp)
        b_term = ExpressionChild.objects.create(parent=ant_exp,child=b_exp)

        r3 = Rule.objects.create(name="r3",label="a + b = c",
                                 antecedent=ant_exp,consequent=c_exp)
        
        self.assertEquals(str(r3), "(AND (a) (b)) => (c)")
        print "trying r3"
        results = entail({a.id : True, 
                          b.id : True})
        self.assertEquals(results[c.id],True)

        d = Predicate.objects.create(name='d',label='d')
        d_exp = d.id_exp()
        ant_exp2 = Expression.objects.create(operator='AND')
        a2_term = ExpressionChild.objects.create(parent=ant_exp2,child=a_exp)
        c_term = ExpressionChild.objects.create(parent=ant_exp2,child=c_exp)
        r4 = Rule.objects.create(name="r4",label="a + c = d",
                                 antecedent=ant_exp2,consequent=d_exp)

        print "trying r3 + r4"
        results = entail({a.id : True, 
                          b.id : True})

        self.assertEquals(results[d.id],True)


        e = Predicate.objects.create(name='e',label='e')
        e_exp = e.id_exp()
        ant_exp3 = Expression.objects.create(operator='AND')
        a3_term = ExpressionChild.objects.create(parent=ant_exp3,child=a_exp)
        d_term = ExpressionChild.objects.create(parent=ant_exp3,child=d_exp)
        r5 = Rule.objects.create(name="r5",label="a + d = e",
                                 antecedent=ant_exp3,consequent=e_exp)

        print "trying r3 + r4 + r5"
        results = entail({a.id : True, 
                          b.id : True})

        self.assertEquals(results[e.id],True)

