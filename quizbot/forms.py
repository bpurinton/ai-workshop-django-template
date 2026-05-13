from django import forms


class TopicForm(forms.Form):
    topic = forms.CharField(
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. The Solar System, Python decorators, World War II",
                "autofocus": "autofocus",
                "class": "topic-input",
            }
        ),
    )

    def clean_topic(self):
        topic = self.cleaned_data["topic"].strip()
        if len(topic) < 2:
            raise forms.ValidationError("Topic must be at least 2 characters.")
        return topic
