# frozen_string_literal: true
require "json"

class DetailSuggester
  def initialize(rng: Random.new)
    @rng = rng
  end

  def suggest(input_hash)
    host = input_hash["host_element"]
    adjacent = input_hash["adjacent_element"]
    exposure = input_hash["exposure"]

    key = [host, adjacent, exposure]
    candidates = details_table[key] || fallback_candidates

    chosen = candidates.sample(random: @rng)

    {
      "suggested_detail" => chosen[:detail],
      "confidence" => random_confidence(chosen[:confidence_range]),
      "reason" => chosen[:reason]
    }
  end

  private

  def details_table
    @details_table ||= {
      ["External Wall", "Slab", "External"] => [
        {
          detail: "External Wall–Slab Junction Waterproofing",
          confidence_range: (0.88..0.95),
          reason: "Matches host/adjacent/exposure; picked from multiple valid details"
        },
        {
          detail: "External Wall–Slab Edge Sealant + Drip Detail",
          confidence_range: (0.80..0.90),
          reason: "Same junction context; alternate commonly used detail"
        }
      ],

      ["Basement Wall", "Slab", "Ground"] => [
        {
          detail: "Basement Wall–Slab Joint Waterbar + Waterproofing",
          confidence_range: (0.85..0.93),
          reason: "Below-grade junction; picked from multiple valid details"
        },
        {
          detail: "Basement Wall–Slab Fillet + Membrane Lapping",
          confidence_range: (0.78..0.88),
          reason: "Below-grade junction; alternate approach"
        }
      ]
    }
  end

  def fallback_candidates
    [
      {
        detail: "Generic Junction Sealing Detail",
        confidence_range: (0.45..0.60),
        reason: "No exact rule; using generic fallback"
      },
      {
        detail: "Generic Waterproofing Continuity Detail",
        confidence_range: (0.40..0.58),
        reason: "No exact rule; using another safe fallback"
      }
    ]
  end

  def random_confidence(range)
    # rounding off to 2 digits.
    min = range.begin.to_f
    max = range.end.to_f
    (min + @rng.rand * (max - min)).round(2)
  end
end

#testing with random input and corresponding output
HOSTS     = ["External Wall", "Basement Wall", "Internal Wall"].freeze
ADJACENTS = ["Slab", "Roof Slab", "Beam"].freeze
EXPOSURES = ["External", "Ground", "Internal"].freeze

input = {
  "host_element" => HOSTS.sample,
  "adjacent_element" => ADJACENTS.sample,
  "exposure" => EXPOSURES.sample
}

suggester = DetailSuggester.new
output = suggester.suggest(input)

puts "INPUT:"
puts JSON.pretty_generate(input)
puts "\nOUTPUT:"
puts JSON.pretty_generate(output)
