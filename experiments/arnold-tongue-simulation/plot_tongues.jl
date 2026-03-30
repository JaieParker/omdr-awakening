# ============================================================
# Arnold Tongue Visualization — Publication Quality
# Reads data from arnold_tongues.jl output, generates figures
#
# Kai, 2026-03-30
# ============================================================

using Plots, DelimitedFiles, Printf

data_dir = joinpath(@__DIR__, "data")
fig_dir = joinpath(@__DIR__, "figures")
mkpath(fig_dir)

# --- Load data ---

println("Loading data...")

# Tongue diagram
lines = readlines(joinpath(data_dir, "tongue_diagram.csv"))
header_lines = count(l -> startswith(l, "#"), lines)
# Parse Ω and K ranges from headers
ω_info = match(r"Ω range: ([\d.]+) to ([\d.]+), N=(\d+)", lines[3])
k_info = match(r"K range: ([\d.]+) to ([\d.]+), N=(\d+)", lines[4])
NΩ = parse(Int, ω_info[3])
NK = parse(Int, k_info[3])
Ωs = range(parse(Float64, ω_info[1]), parse(Float64, ω_info[2]), length=NΩ)
Ks = range(parse(Float64, k_info[1]), parse(Float64, k_info[2]), length=NK)

ρ = zeros(NK, NΩ)
for (i, line) in enumerate(lines[header_lines+1:end])
    vals = parse.(Float64, split(line, ","))
    ρ[i, :] = vals
end

# Devil's staircase
stair_data = readdlm(joinpath(data_dir, "staircase_K025.csv"), ',', Float64, skipstart=1)
Ω_stairs = stair_data[:, 1]
ρ_stairs = stair_data[:, 2]

# Tongue widths
width_data = readdlm(joinpath(data_dir, "tongue_widths_K025.csv"), ',', skipstart=1)

println("Data loaded: $(NK)×$(NΩ) tongue diagram")

# ============================================================
# Figure 1: Arnold Tongue Heatmap
# ============================================================
println("Generating Figure 1: Arnold tongue heatmap...")

p1 = heatmap(collect(Ωs), collect(Ks), ρ,
    xlabel="Ω (frequency ratio)",
    ylabel="K (coupling strength)",
    title="Arnold Tongues — Circle Map",
    colorbar_title="Rotation number ρ",
    color=:twilight,
    clims=(0, 1),
    size=(900, 600),
    dpi=200)

# Mark K=0.25
hline!([0.25], color=:red, lw=2.5, ls=:dash, label="K = 0.25 (OMDR optimal)")

# Annotate major tongues
annotate!(0.5, 0.92, text("1:2", 10, :white, :bold))
annotate!(0.333, 0.92, text("1:3", 8, :white))
annotate!(0.667, 0.92, text("2:3", 8, :white))
annotate!(0.25, 0.92, text("1:4", 7, :white))
annotate!(0.75, 0.92, text("3:4", 7, :white))

savefig(p1, joinpath(fig_dir, "arnold_tongues_heatmap.png"))
println("  Saved: figures/arnold_tongues_heatmap.png")

# ============================================================
# Figure 2: Devil's Staircase at K=0.25
# ============================================================
println("Generating Figure 2: Devil's staircase at K=0.25...")

p2 = plot(Ω_stairs, ρ_stairs,
    xlabel="Ω (driving frequency)",
    ylabel="ρ (rotation number)",
    title="Devil's Staircase at K = 0.25",
    lw=1.5,
    color=:darkblue,
    legend=false,
    size=(900, 500),
    dpi=200)

# Mark consonant ratios
for (p, q, label, col) in [
    (1, 2, "1/2", :red),
    (1, 3, "1/3", :orange),
    (2, 3, "2/3", :orange),
    (1, 4, "1/4", :green),
    (3, 4, "3/4", :green),
    (2, 5, "2/5", :purple),
    (3, 5, "3/5", :purple)]

    hline!([p/q], color=col, alpha=0.3, lw=0.8, label="")
    annotate!(0.02, p/q + 0.015, text(label, 7, col, :left))
end

# Diagonal reference line (no locking)
plot!(Ω_stairs, Ω_stairs, color=:gray, alpha=0.3, ls=:dot, label="")

savefig(p2, joinpath(fig_dir, "devils_staircase_K025.png"))
println("  Saved: figures/devils_staircase_K025.png")

# ============================================================
# Figure 3: Tongue Width vs Farey Order (Consonance Hierarchy)
# ============================================================
println("Generating Figure 3: Consonance hierarchy bar chart...")

# Filter to non-zero widths
nonzero = [(Int(width_data[i,1]), Int(width_data[i,2]), width_data[i,4])
           for i in 1:size(width_data,1) if width_data[i,4] > 0]
sort!(nonzero, by=x->x[3], rev=true)

labels = ["$(w[1])/$(w[2])" for w in nonzero]
widths = [w[3] for w in nonzero]
farey_sums = [w[1] + w[2] for w in nonzero]

# Color by Farey sum
colors = [fs <= 2 ? :red : fs <= 3 ? :orange : fs <= 5 ? :green : :blue
          for fs in farey_sums]

p3 = bar(labels, widths,
    xlabel="Frequency ratio p/q",
    ylabel="Tongue width at K=0.25",
    title="Consonance Hierarchy — Tongue Widths Follow Farey Order",
    color=colors,
    legend=false,
    size=(900, 500),
    dpi=200,
    xrotation=45,
    yscale=:log10)

savefig(p3, joinpath(fig_dir, "consonance_hierarchy.png"))
println("  Saved: figures/consonance_hierarchy.png")

# ============================================================
# Figure 4: Integration vs Differentiation Phase Diagram
# ============================================================
println("Generating Figure 4: Integration/differentiation phase diagram...")

# Compute "locking fraction" at each K
# (fraction of Ω values that are locked to a rational)
function locking_fraction(ρ_row; tol=1e-4)
    locked = 0
    for ρ_val in ρ_row
        # Check if close to a rational p/q with q ≤ 12
        for q in 1:12
            for p in 0:q
                if abs(ρ_val - p/q) < tol
                    locked += 1
                    @goto next
                end
            end
        end
        @label next
    end
    return locked / length(ρ_row)
end

lock_frac = [locking_fraction(ρ[i, :]) for i in 1:NK]
free_frac = 1.0 .- lock_frac

p4 = plot(collect(Ks), lock_frac,
    label="Integration (locked fraction)",
    color=:blue, lw=2,
    xlabel="K (coupling strength)",
    ylabel="Fraction of Ω space",
    title="Integration vs Differentiation — Balance at K ≈ 0.25",
    size=(900, 500),
    dpi=200,
    ylims=(0, 1))

plot!(collect(Ks), free_frac,
    label="Differentiation (free fraction)",
    color=:red, lw=2)

# Mark K=0.25
vline!([0.25], color=:black, lw=2, ls=:dash, label="K = 0.25")

# Mark the crossing / balance region
annotate!(0.27, 0.5, text("← Balance point", 9, :left))

savefig(p4, joinpath(fig_dir, "integration_differentiation.png"))
println("  Saved: figures/integration_differentiation.png")

# ============================================================
println("\n" * "="^60)
println("All figures saved to: $(fig_dir)")
println("="^60)
