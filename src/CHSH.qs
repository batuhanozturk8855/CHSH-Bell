namespace CHSH {

    import Std.Math.*;
    import Std.Arrays.*;

    /// Prepares the Bell state |Phi+> = (|00> + |11>) / sqrt(2).
    operation PrepareBellPair(a : Qubit, b : Qubit) : Unit {
        H(a);
        CNOT(a, b);
    }

    /// Prepares a separable reference state (|+>|+>) with the same
    /// single-qubit statistics as the Bell pair but no entanglement.
    operation PrepareProductPair(a : Qubit, b : Qubit) : Unit {
        H(a);
        H(b);
    }

    /// Measures the observable cos(theta) Z + sin(theta) X.
    /// Rotating by Ry(-theta) maps that axis onto Z, so a plain
    /// Z-measurement afterwards implements the tilted measurement.
    operation MeasureAtAngle(theta : Double, q : Qubit) : Result {
        Ry(-theta, q);
        return MResetZ(q);
    }

    /// One CHSH trial: prepare a pair, measure Alice at angleA and
    /// Bob at angleB, and return the product of the +1 / -1 outcomes.
    operation SampleCorrelation(
        angleA : Double,
        angleB : Double,
        entangled : Bool
    ) : Int {
        use (a, b) = (Qubit(), Qubit());
        if entangled {
            PrepareBellPair(a, b);
        } else {
            PrepareProductPair(a, b);
        }
        let ra = MeasureAtAngle(angleA, a);
        let rb = MeasureAtAngle(angleB, b);
        let sa = ra == Zero ? 1 | -1;
        let sb = rb == Zero ? 1 | -1;
        return sa * sb;
    }

    /// Runs `shots` independent trials and returns the raw +1 / -1 products.
    /// Averaging these in Python gives the correlator E(angleA, angleB).
    operation SampleCorrelationBatch(
        angleA : Double,
        angleB : Double,
        entangled : Bool,
        shots : Int
    ) : Int[] {
        mutable products = [0, size = shots];
        for i in 0..shots - 1 {
            set products w/= i <- SampleCorrelation(angleA, angleB, entangled);
        }
        return products;
    }
}
