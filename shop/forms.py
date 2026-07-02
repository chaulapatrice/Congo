from django import forms

from .models import Rating

RATING_CHOICES = [
    (5, "5 — Excellent"),
    (4, "4 — Good"),
    (3, "3 — Average"),
    (2, "2 — Poor"),
    (1, "1 — Terrible"),
]


class RatingForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=RATING_CHOICES,
        coerce=int,
        label="Rating",
        widget=forms.Select,
    )

    class Meta:
        model = Rating
        fields = ["rating", "content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Share your thoughts about this product..."}
            ),
        }
        labels = {"content": "Your review"}